"""Raw-waveform area-integral drop volume — threshold-independent.

The edge-time pulse duration depends on where the Schmitt threshold sits
relative to the position-specific optical baseline; this is why edge-time
features cannot be position-invariant. The raw-waveform area integral
(∫ (I0 - I(t)) dt) is approximately proportional to drop cross-section
times beam transit time, which depends only on the drop geometry and
velocity — not on where the threshold happens to fall.

For a spherical drop of diameter d passing through a thin beam (slab of
height h << d) at center, the attenuation profile (1 - I(t)/I0) is
proportional to the chord intercept of the sphere at vertical position
v·t. The time-integral evaluates to:

    ∫ (1 - I(t)/I0) dt   ≈   (π / 4) · d² / v             (thin-beam limit)

so:

    d   =   sqrt( (4/π) · v · ∫(1 - I/I0) dt )
    V   =   (π/6) · d³

This script:
1. Loads P3's raw-waveform UART log + paired gravimetric truth (V=49.73 µL).
2. For each drop, identifies the pre-event baseline (median of leading 100
   samples), computes the normalized attenuation integral on the TOP and
   BOT beams, derives d_top and d_bot from each, computes V_top and V_bot.
3. Reports per-drop V_top, V_bot, V_min (auto-contamination-rejection).
4. Compares to V_true and to the firmware-K-1.27 / linear-regression
   baselines.
"""
from __future__ import annotations

import sys
import math
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from algo_replay import parse_uart_log, pair_with_gravimetric, DropEvent  # noqa

REPO = HERE.parents[1]
OUT = REPO / "analysis" / "figs" / "2026-05-14_pm" / "final"
OUT.mkdir(parents=True, exist_ok=True)

TODAY = REPO / "data" / "raw" / "2026-05-14_pm"

BEAM_PITCH_MM = 10.0
G_MMPS2 = 9810.0


def velocity_mmps(ev: DropEvent) -> float:
    """Same physics as firmware/algo_replay: gravity-corrected mid-flight v."""
    dt_s = ev.transit_us * 1e-6
    return BEAM_PITCH_MM / dt_s - 0.5 * G_MMPS2 * dt_s


def area_diameter(raw: np.ndarray, t_us: np.ndarray, baseline_n: int = 100) -> tuple[float, float, dict]:
    """Return (d_mm, integral_seconds, debug) from a single-beam raw trace.

    Approach: baseline = median of the first `baseline_n` samples (the
    pre-drop region). Attenuation profile a(t) = max(0, 1 - I(t)/I0). The
    integral has units of seconds; multiplied by velocity it gives an area
    in mm·s · mm/s = mm² (the shadow area).

    The shadow area of a sphere onto a plane is π/4·d². Solving:
        d = sqrt( (4/π) · ∫a(t) dt · v )   where v is in mm/s, t in s
    """
    if raw.size < baseline_n + 20:
        return float("nan"), float("nan"), {"reason": "too_short"}
    I0 = float(np.median(raw[:baseline_n]))
    if I0 <= 0:
        return float("nan"), float("nan"), {"reason": "I0_zero"}
    a = np.clip(1.0 - raw.astype(float) / I0, 0.0, 1.0)
    # Convert t_us to seconds
    t_s = t_us.astype(float) * 1e-6
    # Trapezoidal integral
    integ_s = float(np.trapezoid(a, t_s))
    return integ_s, I0, {"a_max": float(a.max()), "len": int(raw.size)}


def per_drop_volume_from_area(ev: DropEvent) -> dict:
    if not ev.has_raw:
        return dict(V_top=np.nan, V_bot=np.nan, V_min=np.nan, V_mean=np.nan,
                    d_top=np.nan, d_bot=np.nan, area_top=np.nan, area_bot=np.nan)
    v_mmps = velocity_mmps(ev)
    area_top, _, _ = area_diameter(ev.raw_top, ev.raw_t_us)
    area_bot, _, _ = area_diameter(ev.raw_bot, ev.raw_t_us)
    # d^2 = (4/π) · area_seconds · v_mmps   ; want d in mm
    d_top = math.sqrt((4.0 / math.pi) * area_top * v_mmps) if area_top > 0 else np.nan
    d_bot = math.sqrt((4.0 / math.pi) * area_bot * v_mmps) if area_bot > 0 else np.nan
    V_top = (math.pi / 6.0) * d_top ** 3 if not math.isnan(d_top) else np.nan
    V_bot = (math.pi / 6.0) * d_bot ** 3 if not math.isnan(d_bot) else np.nan
    valid = [v for v in (V_top, V_bot) if not (v is None or math.isnan(v))]
    V_min = min(valid) if valid else np.nan
    V_mean = float(np.mean(valid)) if valid else np.nan
    return dict(V_top=V_top, V_bot=V_bot, V_min=V_min, V_mean=V_mean,
                d_top=d_top, d_bot=d_bot, area_top=area_top, area_bot=area_bot,
                v_mmps=v_mmps)


def main():
    p3_path = TODAY / "p3_minus4mm_run01.uart.log"
    p3 = parse_uart_log(p3_path, position_tag="P3_minus4mm", flow_mlh=50.0)
    p3_scale = pair_with_gravimetric(p3, TODAY / "p3_minus4mm_run01_scale.csv")
    V_true = p3_scale["V_true_per_drop_uL"]
    print(f"P3: {len(p3)} drops, V_true = {V_true:.2f} uL/drop (Mass d={p3_scale['scale_delta_mL']:.4f} g, n_uart={len(p3)})")

    with_raw = [e for e in p3 if e.has_raw]
    print(f"  drops with raw waveform: {len(with_raw)}")
    if with_raw:
        sample_periods = [e.sample_period_us_estimate for e in with_raw]
        print(f"  mean sample period: {np.mean(sample_periods):.2f} us")
        sample_counts = [e.raw_top.size for e in with_raw]
        print(f"  samples per window: min={min(sample_counts)} max={max(sample_counts)}")

    rows = []
    for ev in with_raw:
        r = per_drop_volume_from_area(ev)
        r["drop_n"] = ev.drop_n
        r["transit_us"] = ev.transit_us
        r["pulse_top_us"] = ev.pulse_top_us
        r["pulse_bot_us"] = ev.pulse_bot_us
        rows.append(r)
    df = pd.DataFrame(rows)
    print("\nPer-drop volume from area integral:")
    print(df[["drop_n", "v_mmps", "area_top", "area_bot", "d_top", "d_bot", "V_top", "V_bot", "V_min", "V_mean"]].to_string(index=False, float_format="%.3f"))

    valid = df["V_min"].dropna()
    print(f"\nV_min  : mean={valid.mean():.2f}  median={valid.median():.2f}  std={valid.std():.2f}  n={len(valid)}")
    print(f"  err vs V_true: {100*(valid.mean() - V_true)/V_true:+.1f}%")
    valid_top = df["V_top"].dropna()
    print(f"V_top  : mean={valid_top.mean():.2f}  std={valid_top.std():.2f}  err={100*(valid_top.mean()-V_true)/V_true:+.1f}%")
    valid_bot = df["V_bot"].dropna()
    print(f"V_bot  : mean={valid_bot.mean():.2f}  std={valid_bot.std():.2f}  err={100*(valid_bot.mean()-V_true)/V_true:+.1f}%")
    valid_mean = df["V_mean"].dropna()
    print(f"V_mean : mean={valid_mean.mean():.2f}  std={valid_mean.std():.2f}  err={100*(valid_mean.mean()-V_true)/V_true:+.1f}%")

    # Diagnostic figure: a few example traces
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    axes = axes.flatten()
    sample_drops = with_raw[:6]
    for ax, ev in zip(axes, sample_drops):
        I0_top = float(np.median(ev.raw_top[:100]))
        I0_bot = float(np.median(ev.raw_bot[:100]))
        a_top = np.clip(1.0 - ev.raw_top.astype(float) / I0_top, 0, 1)
        a_bot = np.clip(1.0 - ev.raw_bot.astype(float) / I0_bot, 0, 1)
        t_ms = (ev.raw_t_us - ev.raw_t_us[0]) * 1e-3
        ax.plot(t_ms, a_top, color="#3498db", label="TOP attenuation", linewidth=1.0)
        ax.plot(t_ms, a_bot, color="#e74c3c", label="BOT attenuation", linewidth=1.0, alpha=0.9)
        ax.fill_between(t_ms, 0, a_top, color="#3498db", alpha=0.18)
        ax.fill_between(t_ms, 0, a_bot, color="#e74c3c", alpha=0.18)
        r = per_drop_volume_from_area(ev)
        ax.set_title(f"drop {ev.drop_n}: V_top={r['V_top']:.1f} V_bot={r['V_bot']:.1f} uL", fontsize=9)
        ax.set_xlabel("t (ms)"); ax.set_ylabel("attenuation a(t)")
        ax.legend(fontsize=7)
        ax.set_ylim(0, 1.05)
    fig.suptitle(f"P3 (-4 mm) — raw attenuation profiles, area-integral volume estimate (V_true={V_true:.1f} uL)")
    fig.tight_layout()
    fig.savefig(OUT / "fig6_p3_raw_attenuation_profiles.png", dpi=140)
    plt.close(fig)

    # Headline bar chart vs other methods
    fig, ax = plt.subplots(figsize=(9, 4.8))
    methods = ["firmware\nK=1.27", "refit global\nK=0.54", "linear regression\n(chord_min+v)", "area-integral\nV_min (NEW)"]
    means = [231.40, 98.18, 70.51, valid.mean()]
    stds = [14.33, 6.08, 0.33, valid.std()]
    colors = ["#c0392b", "#e67e22", "#f1c40f", "#27ae60"]
    bars = ax.bar(methods, means, yerr=stds, capsize=6, color=colors, alpha=0.9)
    ax.axhline(V_true, color="k", linestyle="--", label=f"V_true gravimetric = {V_true:.1f} uL")
    ax.fill_between([-0.5, 3.5], V_true*0.9, V_true*1.1, color="grey", alpha=0.15, label="±10 %")
    ax.fill_between([-0.5, 3.5], V_true*0.95, V_true*1.05, color="grey", alpha=0.25, label="±5 %")
    for i, (m, s) in enumerate(zip(means, stds)):
        err_pct = 100 * (m - V_true) / V_true
        ax.text(i, m + s + 5, f"{err_pct:+.1f}%", ha="center", fontsize=9, fontweight="bold")
    ax.set_xlim(-0.5, 3.5)
    ax.set_ylabel("mean V_est ± 1σ (uL/drop)")
    ax.set_title(f"P3 (-4 mm) blind test — 4 algorithms vs gravimetric truth, n={len(valid)}")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig7_p3_area_vs_others.png", dpi=140)
    plt.close(fig)

    # Write summary
    out = []
    out.append(f"=== Raw-waveform area-integral volume — P3 ({len(valid)} drops) ===")
    out.append(f"V_true (gravimetric)  = {V_true:.2f} uL/drop")
    out.append(f"V_top  (area + d^3)   = {valid_top.mean():6.2f} ± {valid_top.std():5.2f}  err = {100*(valid_top.mean()-V_true)/V_true:+5.1f}%")
    out.append(f"V_bot  (area + d^3)   = {valid_bot.mean():6.2f} ± {valid_bot.std():5.2f}  err = {100*(valid_bot.mean()-V_true)/V_true:+5.1f}%")
    out.append(f"V_min  (auto-clean)   = {valid.mean():6.2f} ± {valid.std():5.2f}  err = {100*(valid.mean()-V_true)/V_true:+5.1f}%")
    out.append(f"V_mean (top+bot avg)  = {valid_mean.mean():6.2f} ± {valid_mean.std():5.2f}  err = {100*(valid_mean.mean()-V_true)/V_true:+5.1f}%")
    out.append("")
    out.append("vs other methods (same P3 dataset):")
    out.append(f"  firmware K=1.27                   = 231.40 uL  err = +365.3%")
    out.append(f"  refit global K=0.54               =  98.18 uL  err =  +97.4%")
    out.append(f"  linear regression (chord_min+v)   =  70.51 uL  err =  +41.8%")
    out.append(f"  area-integral V_min (NEW)         = {valid.mean():.2f} uL  err = {100*(valid.mean()-V_true)/V_true:+.1f}%")
    txt = "\n".join(out)
    (OUT / "summary_p3_area.txt").write_text(txt, encoding="utf-8")
    print("\n" + txt)


if __name__ == "__main__":
    main()
