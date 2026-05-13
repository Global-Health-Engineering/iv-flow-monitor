#!/usr/bin/env python3
"""Per-drop matching of UART DROP events to scale-stream mass steps.

DEPRECATED for ground-truth purposes — kept as an exploratory diagnostic
only. See `docs/limitations.md` §"Two-orifice divergence".

The dual-orifice problem
------------------------
The device measures drops at the **drip-chamber orifice** (where they
form). The scale captures mass at the **end-of-tubing orifice** (where
they fall out into the catch vessel). These two orifices have different
geometry, different surface-tension dynamics, and different drop sizes,
so:

    N_chamber × V_chamber  =  N_end × V_end  =  total mass

but **N_chamber ≠ N_end** and the chamber drops and end-orifice drops
cannot be matched 1:1. A given chamber drop adds mass to the tubing; the
end orifice releases that mass on its own dripping schedule. The 2026-05-13
campaign saw scale step counts up to 2× the UART drop counts — that is
the end orifice dripping with smaller drop volume, not the device missing
half its drops.

The valid ground truth at this granularity is therefore the **per-run
chamber-drop average**:

    V_true_chamber = total_mass_g × 1000 / N_UART        (µL per chamber drop)

which is what `analysis/scripts/load_run.py` uses and what
`docs/results.md` reports. This script remains useful for inspecting the
end-orifice drop-rate behaviour, but the per-drop "Bland-Altman" pairing
it produces is not a measurement of device accuracy.

Algorithm
---------
1. Step detection on the smoothed scale signal:
   - Smooth with a small median filter (kills the transient overshoot
     spike that lands during drop impact).
   - Find rising-edge events where smoothed mass increases by > MIN_STEP
     over a short window (the drop landing).
2. Per step: compute "before" mass (median of N samples immediately
   before the rise) and "after" mass (median of N samples once the
   post-landing oscillation settles). Increment = after − before.
3. Pair each scale step with the closest UART DROP event by host time
   (allowing FALL_LATENCY_MS of fall-then-settle delay). Each event
   matched at most once.
4. Emit a CSV with one row per matched pair: t_uart_ms, t_scale_ms,
   dt_us, pulse_top_us, pulse_bot_us, v_est_uL (from load_run.py),
   v_true_uL (from scale step).

The scale stream's t_ms starts at the same wall-clock moment as the
UART capture (the bench orchestrator launches them within ~1 s), so
matching by elapsed-since-start time is robust without explicit clock
sync.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "analysis"))
from scripts.load_run import load_run  # noqa: E402

# Tuning constants. These are physics-grounded rather than per-bench knobs:
# - MIN_STEP_G:        smallest drop the scale can reliably resolve above
#                      its drift floor. ~10 mg covers all drip sets down to
#                      micro 60 gtt/mL (17 µL/drop).
# - PRE_WINDOW_MS:     duration of "before" plateau used to baseline a step.
#                      300 ms covers ~7 scale samples at 23 Hz, robust to a
#                      single outlier sample.
# - SETTLE_MS:         time after the step before "after" plateau is read.
#                      The scale transient overshoot decays in ~1 s on the
#                      MS-series; reading after that gives the true settled
#                      mass.
# - POST_WINDOW_MS:    duration of "after" plateau.
# - FALL_LATENCY_MS:   maximum time between UART DROP event (drop crosses
#                      BOT beam) and the scale step (drop lands in vessel).
#                      Drop falls ~5-15 cm from BOT beam to scale; flight
#                      time ~0.1-0.2 s; scale signal rise takes ~0.05 s
#                      more. Allow up to 600 ms.
MIN_STEP_G = 0.010
PRE_WINDOW_MS = 300
SETTLE_MS = 1000
POST_WINDOW_MS = 400
FALL_LATENCY_MS = 600


def detect_steps(scale_df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame of detected scale steps with columns:
    t_step_ms, mass_before_g, mass_after_g, delta_g.
    """
    t = scale_df["t_ms"].to_numpy()
    m = scale_df["mass_g"].to_numpy()

    # Resample to a uniform grid so window logic is simpler.
    t0, t1 = float(t[0]), float(t[-1])
    grid_ms = np.arange(t0, t1, 25.0)  # 40 Hz uniform grid (scale ~ 23 Hz)
    m_grid = np.interp(grid_ms, t, m)

    # 5-sample (~125 ms) median filter to smear the transient overshoot
    # without erasing the underlying step.
    from scipy.signal import medfilt
    try:
        m_smooth = medfilt(m_grid, kernel_size=5)
    except Exception:
        # Fallback if scipy isn't available: simple moving median.
        win = 5
        m_smooth = np.array([np.median(m_grid[max(0, i - win // 2):
                                              min(len(m_grid), i + win // 2 + 1)])
                             for i in range(len(m_grid))])

    # Slope: first difference. Drops produce a sharp positive slope window.
    dm = np.diff(m_smooth, prepend=m_smooth[0])

    # Detect rising-edge events: dm above threshold AND surrounded by quieter
    # samples on each side. Use a windowed running max to find local peaks.
    # Each detected peak counts as one drop.
    rising = dm > (MIN_STEP_G * 0.6)  # at least 60% of MIN_STEP in one sample

    steps = []
    i = 0
    n = len(m_smooth)
    pre_n = max(2, PRE_WINDOW_MS // 25)
    settle_n = max(2, SETTLE_MS // 25)
    post_n = max(2, POST_WINDOW_MS // 25)
    while i < n:
        if not rising[i]:
            i += 1
            continue
        # Found a rise. Walk forward while still rising or until a small gap.
        rise_start = i
        while i < n and rising[i]:
            i += 1
        rise_end = i

        # Before-window plateau: median of pre_n samples before rise_start.
        lo = max(0, rise_start - pre_n)
        mass_before = float(np.median(m_smooth[lo:rise_start])) if rise_start > lo else float(m_smooth[rise_start])

        # After-window plateau: skip the settle window, then sample post_n.
        after_lo = min(n - 1, rise_end + settle_n)
        after_hi = min(n, after_lo + post_n)
        if after_hi <= after_lo + 1:
            i = rise_end + 1
            continue
        mass_after = float(np.median(m_smooth[after_lo:after_hi]))
        delta = mass_after - mass_before
        if delta >= MIN_STEP_G:
            steps.append({
                "t_step_ms": float(grid_ms[rise_start]),
                "mass_before_g": mass_before,
                "mass_after_g": mass_after,
                "delta_g": delta,
            })
        # Skip past the settle window before looking for the next step
        i = max(i, after_lo)

    return pd.DataFrame(steps)


def match_drops(uart_df: pd.DataFrame, steps_df: pd.DataFrame,
                uart_t0_ms: float | None = None,
                ) -> pd.DataFrame:
    """Greedy nearest-neighbour matching of UART drops to scale steps.

    Both inputs must have an absolute or run-relative timestamp. UART
    timestamps come from `abs_ms` (firmware uptime since boot) so we
    normalise to "ms since first drop in this CSV" before matching.
    """
    if uart_t0_ms is None:
        uart_t0_ms = float(uart_df["abs_ms"].iloc[0])
    uart_t = (uart_df["abs_ms"].to_numpy() - uart_t0_ms).astype(float)
    step_t = steps_df["t_step_ms"].to_numpy()
    used = np.zeros(len(step_t), dtype=bool)
    rows = []
    for k, drop_t in enumerate(uart_t):
        # Look for the closest unused scale step in [drop_t, drop_t + FALL_LATENCY_MS].
        candidates = np.where((~used) & (step_t >= drop_t - 100.0) & (step_t <= drop_t + FALL_LATENCY_MS))[0]
        if len(candidates) == 0:
            rows.append({
                "uart_idx": k,
                "step_idx": -1,
                "t_uart_rel_ms": drop_t,
                "t_step_rel_ms": float("nan"),
                "delta_g": float("nan"),
                "matched": False,
            })
            continue
        # Pick nearest in time.
        j = int(candidates[np.argmin(np.abs(step_t[candidates] - drop_t))])
        used[j] = True
        rows.append({
            "uart_idx": k,
            "step_idx": j,
            "t_uart_rel_ms": drop_t,
            "t_step_rel_ms": float(step_t[j]),
            "delta_g": float(steps_df["delta_g"].iloc[j]),
            "matched": True,
        })
    # Unused scale steps = scale-detected drops that the firmware missed.
    for j in np.where(~used)[0]:
        rows.append({
            "uart_idx": -1,
            "step_idx": j,
            "t_uart_rel_ms": float("nan"),
            "t_step_rel_ms": float(step_t[j]),
            "delta_g": float(steps_df["delta_g"].iloc[j]),
            "matched": False,
        })
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device-csv", required=True)
    ap.add_argument("--scale-csv", required=True)
    ap.add_argument("--beam-mm", type=float, default=10.2)
    ap.add_argument("--density", type=float, default=1.000)
    ap.add_argument("--out-csv", default=None,
                    help="default: alongside device-csv, suffix _perdrop.csv")
    args = ap.parse_args()

    device_csv = Path(args.device_csv).resolve()
    scale_csv = Path(args.scale_csv).resolve()
    if not device_csv.exists():
        print(f"ERROR: {device_csv} not found", file=sys.stderr); return 2
    if not scale_csv.exists():
        print(f"ERROR: {scale_csv} not found", file=sys.stderr); return 2

    drops = load_run(device_csv, beam_separation_mm=args.beam_mm)
    n_uart = len(drops)
    scale_df = pd.read_csv(scale_csv)

    steps_df = detect_steps(scale_df)
    n_steps = len(steps_df)
    matches = match_drops(drops.reset_index(drop=True), steps_df)

    matched = matches[matches["matched"]].copy()
    matched["v_est_uL"] = matched["uart_idx"].apply(
        lambda i: float(drops["drop_volume_uL"].iloc[int(i)]))
    matched["v_true_uL"] = matched["delta_g"] * 1000.0 / args.density
    matched["v_diff_uL"] = matched["v_est_uL"] - matched["v_true_uL"]
    matched["t_lag_ms"] = matched["t_step_rel_ms"] - matched["t_uart_rel_ms"]

    print(f"UART drops:    {n_uart}")
    print(f"Scale steps:   {n_steps}")
    print(f"Matched pairs: {len(matched)}")
    print(f"UART unmatched (firmware-only): {n_uart - len(matched)}")
    print(f"Scale unmatched (missed by firmware): {n_steps - len(matched)}")
    if len(matched):
        print(f"\nPer-drop V_true stats (gravimetric step):")
        print(f"  range  {matched['v_true_uL'].min():.2f}-{matched['v_true_uL'].max():.2f} µL")
        print(f"  mean   {matched['v_true_uL'].mean():.2f} µL")
        print(f"  sd     {matched['v_true_uL'].std(ddof=1):.2f} µL")
        print(f"  CV     {matched['v_true_uL'].std(ddof=1) / matched['v_true_uL'].mean() * 100:.2f} %")
        print(f"\nPer-drop V_est stats (device, load_run.py simple model):")
        print(f"  range  {matched['v_est_uL'].min():.2f}-{matched['v_est_uL'].max():.2f} µL")
        print(f"  mean   {matched['v_est_uL'].mean():.2f} µL")
        print(f"  sd     {matched['v_est_uL'].std(ddof=1):.2f} µL")
        print(f"  CV     {matched['v_est_uL'].std(ddof=1) / matched['v_est_uL'].mean() * 100:.2f} %")
        print(f"\nPer-drop bias: {matched['v_diff_uL'].mean():+.2f} ± {matched['v_diff_uL'].std(ddof=1):.2f} µL")
        sd = matched["v_diff_uL"].std(ddof=1)
        bias = matched["v_diff_uL"].mean()
        print(f"95% LoA: [{bias - 1.96 * sd:+.2f}, {bias + 1.96 * sd:+.2f}] µL")
        print(f"Per-drop MAPE: "
              f"{(matched['v_diff_uL'].abs() / matched['v_true_uL']).mean() * 100:.2f} %")
        print(f"Lag UART→scale: mean {matched['t_lag_ms'].mean():.0f} ms, "
              f"sd {matched['t_lag_ms'].std(ddof=1):.0f} ms")

    out_csv = (Path(args.out_csv).resolve() if args.out_csv else
               device_csv.with_name(device_csv.stem + "_perdrop.csv"))
    matched_out = matched[["uart_idx", "step_idx", "t_uart_rel_ms", "t_step_rel_ms",
                           "t_lag_ms", "delta_g", "v_true_uL", "v_est_uL", "v_diff_uL"]]
    matched_out.to_csv(out_csv, index=False)
    print(f"\nMatched pairs: {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
