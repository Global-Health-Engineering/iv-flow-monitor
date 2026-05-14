#!/usr/bin/env python3
"""Render the 2026-05-13 pm position-dependence figures for docs/limitations.md §17.

Reads the eleven afternoon runs from `data/raw/2026-05-13_pm_position_drift/`
(plus the morning V_50_01..05 calibration runs for reference) and produces
three figures:

  fig_position_K_required.png
      Bar chart of K_required = V_true / V_est_uncorrected per run. Spans
      0.28 -- 1.61 across positions, killing the universal-K hypothesis.

  fig_position_algorithm_scatter.png
      Per-drop V from each algorithm variant (TOP_low, BOT_low, BOT_core,
      hybrid) vs gravimetric truth across all afternoon runs. Each algorithm
      is one panel. The y = x diagonal shows where the algorithm would be
      universally correct.

  fig_position_splash_regime.png
      Per-drop pulse_BOT_low vs pulse_TOP_low scatter coloured by run.
      Splash regime (BOT/TOP > 1.5) shaded; gravity-expected ratio 0.92
      marked. Three regimes visible: clean (near diagonal), umbilical at
      TOP (both pulses inflated, ratio ~ 1), splash at BOT (BOT pulse
      inflated, ratio > 1.5).

Outputs land in `analysis/figures/` next to the existing
`fig_error_budget_with_bench.png`. The whole script is one shot — runs in
~5 s with no external dependencies beyond pandas / matplotlib (both already
pinned in `analysis/requirements.txt`).

Usage:
    python tools/build_position_overlay.py
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "raw" / "2026-05-13_pm_position_drift"
FIG_DIR = REPO_ROOT / "analysis" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

G = 9.81
L_M = 0.0102  # beam separation, geometry.json mean

# Manually curated run summary table — each run's K (firmware constant during the
# capture), gravimetric mass delta, captured drop count, position label.
RUNS = [
    # tag, K, drops, scale_mL, lcd_mL, position_label, algorithm
    ("baseline_k127", 1.27, 19, 1.0145, 2.8666, "low", "old_mean_pulse"),
    ("iter1_k041",    0.41, 19, 1.0256, 0.7432, "low", "old_mean_pulse"),
    ("iter2_k0566",   0.566, 18, 0.9441, 0.9577, "low", "old_mean_pulse"),
    ("iter2_confirm", 0.566, 18, 0.9485, 0.9826, "low", "old_mean_pulse"),
    ("iter3_repos_k0283", 0.283, 16, 0.8278, 0.5556, "new", "old_mean_pulse"),
    ("iter5_bot_core_only", 1.00, 14, 0.7526, 0.7617, "low", "BOT_core"),
    ("iter5b_top_low_highpos", 1.00,  9, 0.7092, 0.3580, "high_splash", "TOP_low"),
    ("iter5b_pos3_top_low",   1.00, 14, 0.7178, 1.2225, "mid_low", "TOP_low"),
    ("iter7_hybrid_pos3",     1.00, 13, 0.6757, 0.5229, "mid_low", "hybrid"),
    ("iter7b_stable",         1.00, 11, 0.6787, 0.4480, "mid_low", "hybrid"),
]

# Morning V_50 calibration runs from docs/results.md (reference points)
V_50 = [
    ("V_50_01", 1.27,  65, 4.7992, 58.35 * 65 / 1000, "morning_pos", "old_mean_pulse"),
    ("V_50_02", 1.27, 339, 13.3097, 49.84 * 339 / 1000, "morning_pos", "old_mean_pulse"),
    ("V_50_03", 1.27, 180, 10.6780, 57.29 * 180 / 1000, "morning_pos", "old_mean_pulse"),
    ("V_50_04", 1.27,  40,  7.4441, 208.44 * 40 / 1000, "morning_pos", "old_mean_pulse"),
    ("V_50_05", 1.27, 153, 7.9481, 41.59 * 153 / 1000, "morning_pos", "old_mean_pulse"),
]

POS_COLORS = {
    "morning_pos": "#1f77b4",
    "low":         "#2ca02c",
    "mid_low":     "#ff7f0e",
    "new":         "#d62728",
    "high_splash": "#9467bd",
}
POS_ORDER = ["morning_pos", "low", "mid_low", "new", "high_splash"]


# --------------------------------------------------------------------- 1. K
def fig_K_required() -> Path:
    """Bar chart of K_required to hit truth per run.

    K_required = V_true / V_est_uncalibrated. V_est_uncalibrated = LCD_mL / K
    (since LCD = chord_sphere_volume × K). So K_required = K × scale / LCD.
    """
    rows = []
    for tag, K, drops, scale_mL, lcd_mL, pos, algo in V_50 + RUNS:
        if lcd_mL <= 0 or drops <= 0:
            continue
        K_req = K * scale_mL / lcd_mL
        rows.append({"tag": tag, "K_required": K_req, "position": pos, "algorithm": algo})
    df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
    df["color"] = df["position"].map(POS_COLORS)
    bars = ax.bar(range(len(df)), df["K_required"], color=df["color"], edgecolor="black", linewidth=0.5)

    # Annotate the V_CAL_K=1.27 value the firmware was originally shipped with
    ax.axhline(1.27, color="#888", linestyle="--", linewidth=1.0, zorder=0)
    ax.text(len(df) - 0.5, 1.30, "V_CAL_K = 1.27 (committed)", ha="right",
            va="bottom", color="#444", fontsize=9)

    # Highlight the K_required range
    ax.axhspan(df["K_required"].min(), df["K_required"].max(),
               color="#fce8d8", alpha=0.35, zorder=-1,
               label=f"observed K range: {df['K_required'].min():.2f} – {df['K_required'].max():.2f}")
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df["tag"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("K required to fit gravimetric (= K × scale / LCD)")
    K_min, K_max = df["K_required"].min(), df["K_required"].max()
    ax.set_title(f"K required to hit ±0 % spans {K_min:.2f} – {K_max:.2f} across "
                 f"{len(df)} bench runs\n"
                 "(same drip set, same board, four different mount positions)")

    # Legend for positions
    handles = [plt.Rectangle((0, 0), 1, 1, color=POS_COLORS[p], label=p) for p in POS_ORDER]
    ax.legend(handles=handles, loc="upper left", title="position",
              fontsize=9, title_fontsize=9, framealpha=0.95)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.set_ylim(0, max(df["K_required"].max(), 1.7) + 0.1)

    out = FIG_DIR / "fig_position_K_required.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


# --------------------------------------------------------- 2. Algorithm scatter
def fig_algorithm_scatter() -> Path:
    """V_LCD per drop (from each algorithm) vs V_true.

    Truth is the run's gravimetric average per drop; the same value is used
    for every drop in that run (we don't have per-drop ground truth — see
    docs/limitations.md §2, the two-orifice divergence).

    Reads pulse_TOP_low / pulse_BOT_low from the *_uart.log DROP rows, plus
    the EVT,PULSES,... lines for tau_hi / bot_hi when available.
    """
    drop_re = re.compile(r"^DROP,(\d+),(\d+),(\d+),(\d+),(\d+),(-?\d+),(-?\d+),(-?\d+),(\d+),(-?\d+),(\d+),(\d+)$")
    evt_re = re.compile(r"PULSES,tau_lo_us=(\d+),tau_hi_us=(\d+),bot_lo_us=(\d+),bot_hi_us=(\d+)")

    rows = []
    for tag, K, drops, scale_mL, lcd_mL, pos, _algo in RUNS:
        log = DATA_DIR / f"{tag}_uart.log"
        if not log.exists() or drops == 0:
            continue
        v_true = scale_mL * 1000.0 / drops    # µL per drop
        text = log.read_text(encoding="utf-8", errors="replace").splitlines()
        # Match DROP and PULSES lines in time-stream order; the PULSES line
        # immediately follows its DROP line in the firmware emission order.
        last_drop = None
        for ln in text:
            ln_body = ln.split("\t")[-1] if "\t" in ln else ln
            m = drop_re.match(ln_body)
            if m:
                last_drop = {
                    "abs_ms":   int(m.group(1)),
                    "drop_N":   int(m.group(2)),
                    "transit":  int(m.group(3)),
                    "p_top_lo": int(m.group(4)),
                    "p_bot_lo": int(m.group(5)),
                    "v_cmps":   int(m.group(6)),
                    "V_LCD_uL": int(m.group(8)) / 10.0,
                    "state":    int(m.group(9)),
                }
                continue
            m = evt_re.search(ln_body)
            if m and last_drop is not None:
                last_drop["p_top_hi"] = int(m.group(2))
                last_drop["p_bot_hi"] = int(m.group(4))
                rows.append({
                    "tag": tag, "position": pos, "v_true_uL": v_true,
                    **last_drop,
                })
                last_drop = None
        if last_drop is not None:
            # final DROP without a PULSES (older firmware): still record
            rows.append({"tag": tag, "position": pos, "v_true_uL": v_true,
                         **last_drop,
                         "p_top_hi": None, "p_bot_hi": None})

    df = pd.DataFrame(rows)
    # Filter out physically implausible rows (likely stale-timestamp artefacts
    # from missed drops). Real drops have pulses 2-12 ms; cap at 25 ms.
    plausible = ((df["p_top_lo"] < 25000) & (df["p_bot_lo"] < 25000)
                 & (df["p_top_lo"] > 500) & (df["p_bot_lo"] > 500))
    n_dropped = (~plausible).sum()
    if n_dropped:
        print(f"  (dropped {n_dropped} drops with implausible pulses)")
    df = df[plausible].copy()

    # Compute alternative algorithm volumes from the raw fields
    def chord_to_V(pulse_us, v_cmps):
        v = v_cmps / 100.0  # m/s
        t = pulse_us / 1e6
        chord_m = v * t + 0.5 * G * t * t
        return (math.pi / 6.0) * (chord_m * 1000) ** 3   # µL

    df["V_TOP_low"]  = df.apply(lambda r: chord_to_V(r["p_top_lo"], r["v_cmps"]), axis=1)
    df["V_BOT_low"]  = df.apply(lambda r: chord_to_V(r["p_bot_lo"], r["v_cmps"]), axis=1)
    df["V_TOP_core"] = df.apply(lambda r: chord_to_V(r["p_top_hi"], r["v_cmps"])
                                if r.get("p_top_hi") and r["p_top_hi"] > 100 else np.nan, axis=1)
    df["V_BOT_core"] = df.apply(lambda r: chord_to_V(r["p_bot_hi"], r["v_cmps"])
                                if r.get("p_bot_hi") and r["p_bot_hi"] > 100 else np.nan, axis=1)
    df["V_mean_low"] = df.apply(lambda r: chord_to_V((r["p_top_lo"] + r["p_bot_lo"]) / 2,
                                                     r["v_cmps"]), axis=1)

    algos = [
        ("V_TOP_low",  "TOP pulse (low thresh)"),
        ("V_BOT_low",  "BOT pulse (low thresh)"),
        ("V_BOT_core", "BOT pulse (core thresh)"),
        ("V_mean_low", "Mean of TOP/BOT (low) — original Rev-B firmware"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(11, 9), constrained_layout=True,
                             sharex=True, sharey=True)
    axes = axes.flatten()

    # Clip y-axis to a realistic drop-volume range so the splash outliers
    # don't squash the cluster. Splash-regime BOT_low can hit 500+ µL; the
    # plot annotates them as off-scale instead of showing them on-axis.
    vmax = 200.0
    n_offscale = ((df["V_BOT_low"] > vmax) | (df["V_mean_low"] > vmax)
                  | (df["V_TOP_low"] > vmax)).sum()
    for ax, (col, title) in zip(axes, algos):
        valid = df[col].notna()
        for pos in POS_ORDER:
            sub = df[(df["position"] == pos) & valid]
            if len(sub) == 0:
                continue
            # Mark off-scale (> vmax) with up-triangles at the y=vmax line
            off = sub[col] > vmax
            on  = sub[col] <= vmax
            if on.any():
                ax.scatter(sub.loc[on, "v_true_uL"], sub.loc[on, col],
                           s=22, alpha=0.7, color=POS_COLORS.get(pos, "gray"),
                           label=pos, edgecolor="white", linewidth=0.4)
            if off.any():
                ax.scatter(sub.loc[off, "v_true_uL"], [vmax * 0.97] * off.sum(),
                           s=42, alpha=0.7, color=POS_COLORS.get(pos, "gray"),
                           marker="^", edgecolor="black", linewidth=0.5)
        ax.plot([0, vmax], [0, vmax], "k--", linewidth=0.8, alpha=0.5)
        # ±5 % band relative to y=x
        x = np.linspace(0, vmax, 100)
        ax.fill_between(x, 0.95 * x, 1.05 * x, color="green", alpha=0.10, label="±5 %")
        ax.set_title(title, fontsize=10)
        ax.grid(linestyle=":", alpha=0.4)
        ax.set_xlim(0, vmax)
        ax.set_ylim(0, vmax)
        if ax in axes[2:]:
            ax.set_xlabel("V_true (gravimetric, µL/drop)")
        if ax in (axes[0], axes[2]):
            ax.set_ylabel("V_LCD (algorithm output, µL/drop)")

    axes[0].legend(loc="upper left", fontsize=8, title="position",
                   title_fontsize=8, framealpha=0.9)
    fig.suptitle("Per-drop V from each algorithm vs gravimetric truth\n"
                 "(2026-05-13 pm campaign, 11 runs, ~150 drops total)", fontsize=11)
    out = FIG_DIR / "fig_position_algorithm_scatter.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


# ----------------------------------------------------------- 3. Splash regime
def fig_splash_regime() -> Path:
    """pulse_BOT_low vs pulse_TOP_low scatter, splash regime highlighted."""
    drop_re = re.compile(r"^DROP,(\d+),(\d+),(\d+),(\d+),(\d+),(-?\d+),(-?\d+),(-?\d+),(\d+),(-?\d+),(\d+),(\d+)$")
    rows = []
    for tag, K, drops, scale_mL, lcd_mL, pos, _algo in RUNS:
        log = DATA_DIR / f"{tag}_uart.log"
        if not log.exists():
            continue
        for ln in log.read_text(encoding="utf-8", errors="replace").splitlines():
            body = ln.split("\t")[-1] if "\t" in ln else ln
            m = drop_re.match(body)
            if not m:
                continue
            p_top, p_bot = int(m.group(4)), int(m.group(5))
            if 500 <= p_top < 25000 and 500 <= p_bot < 25000:
                rows.append({"tag": tag, "position": pos,
                             "p_top": p_top, "p_bot": p_bot})
    df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(8.5, 7.5), constrained_layout=True)
    x = np.array([0, 12000])
    # Splash region: BOT > 1.5 × TOP
    ax.fill_between(x, 1.5 * x, 3 * x, color="#9467bd", alpha=0.12,
                    label="splash regime (BOT/TOP > 1.5)")
    # Gravity-expected line: BOT/TOP = 0.92
    ax.plot(x, 0.92 * x, color="#444", linestyle=":", linewidth=1.0,
            label="gravity-expected (BOT/TOP = 0.92)")
    # 1:1 reference
    ax.plot(x, x, color="black", linestyle="--", linewidth=0.8, alpha=0.4,
            label="BOT = TOP (no asymmetry)")
    # Umbilical region: TOP > 5000 (specific to this drip set / fluid)
    # — note as a band
    ax.axvspan(5500, 8500, color="#ff7f0e", alpha=0.06,
               label="TOP-umbilical band (drop not detached at TOP)")

    for pos in POS_ORDER:
        sub = df[df["position"] == pos]
        if len(sub) == 0:
            continue
        ax.scatter(sub["p_top"], sub["p_bot"], s=18, alpha=0.6,
                   color=POS_COLORS.get(pos, "gray"), label=pos,
                   edgecolor="white", linewidth=0.4)

    ax.set_xlim(0, 11000)
    ax.set_ylim(0, 11000)
    ax.set_xlabel("pulse_TOP (low threshold, µs)")
    ax.set_ylabel("pulse_BOT (low threshold, µs)")
    ax.set_title("Per-drop pulse_BOT vs pulse_TOP across afternoon positions\n"
                 "Splash and umbilical regimes occupy disjoint parts of the plane")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax.grid(linestyle=":", alpha=0.4)
    ax.set_aspect("equal")

    out = FIG_DIR / "fig_position_splash_regime.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main():
    print(f"Repo root: {REPO_ROOT}")
    print(f"Data dir:  {DATA_DIR}")
    print(f"Fig dir:   {FIG_DIR}")
    print()
    p1 = fig_K_required()
    print(f"  Wrote {p1.relative_to(REPO_ROOT)}")
    p2 = fig_algorithm_scatter()
    print(f"  Wrote {p2.relative_to(REPO_ROOT)}")
    p3 = fig_splash_regime()
    print(f"  Wrote {p3.relative_to(REPO_ROOT)}")
    print()
    print("Done. See docs/limitations.md §17 for the interpretation.")


if __name__ == "__main__":
    main()
