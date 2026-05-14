"""Pure-physics drop volume — V = pi/6 * chord_min^3, no K, no regression.

Insight after the area-integral attempt failed: V = (pi/6) * chord_min^3
gives 44.5 uL at P3 vs V_true=49.7 uL (only -10.5% error) using the
SHORTER of (pulse_top, pulse_bot) on the standard-threshold firmware
build. This is the right physics: the cleaner beam (un-contaminated by
splash or umbilical) gives the true horizontal chord at the moment of
transit, and V = pi/6 * d^3 for a sphere of that diameter.

This script:
1. Categorises yesterday's runs by firmware-threshold variant.
2. Runs pure-physics V_uL = (pi/6) * chord_min^3 on STANDARD-THRESHOLD
   runs from yesterday + P3 today.
3. Reports per-position error against V_true.
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

YEST = REPO / "data" / "raw" / "2026-05-13_pm_position_drift"
TODAY = REPO / "data" / "raw" / "2026-05-14_pm"

BEAM_PITCH_MM = 10.0
G_MMPS2 = 9810.0

# Standard threshold firmware = baseline_k127 and the V_CAL_K-only variants
# (iter1, iter2, iter2_confirm, iter3) which only changed the volume rescaling
# constant K, leaving Schmitt threshold positions unchanged. iter5* and iter7*
# changed the threshold logic itself (BOT-core, TOP-low, hybrid) and produce
# pulse durations that are not comparable.
STANDARD = [
    ("baseline_k127",     "low_post_overnight",  53.14),
    ("iter1_k041",        "low_post_overnight",  53.14),
    ("iter2_k0566",       "low_post_overnight",  53.14),
    ("iter2_confirm",     "low_post_overnight",  53.14),
    ("iter3_repos_k0283", "new_remount",         51.74),
]


def velocity_mmps(ev: DropEvent) -> float:
    dt_s = ev.transit_us * 1e-6
    return BEAM_PITCH_MM / dt_s - 0.5 * G_MMPS2 * dt_s


def chord_min(ev: DropEvent) -> float:
    """Chord through the cleaner of (TOP, BOT) beams, gravity-corrected."""
    v = velocity_mmps(ev)
    tau_top = ev.pulse_top_us * 1e-6
    tau_bot = ev.pulse_bot_us * 1e-6
    c_top = v * tau_top + 0.5 * G_MMPS2 * tau_top ** 2
    c_bot = v * tau_bot + 0.5 * G_MMPS2 * tau_bot ** 2
    return min(c_top, c_bot)


def V_pure(ev: DropEvent) -> float:
    d = chord_min(ev)
    if d <= 0:
        return float("nan")
    return (math.pi / 6.0) * d ** 3


def collect(runs, root):
    rows = []
    pos_truth = {}
    for tag, pos, V_true in runs:
        # Today's captures use "<tag>.uart.log" (dot); yesterday's use
        # "<tag>_uart.log" (underscore). Try both.
        u = root / f"{tag}.uart.log"
        if not u.exists():
            u = root / f"{tag}_uart.log"
        s = root / f"{tag}_scale.csv"
        if not u.exists():
            print(f"  miss {tag}"); continue
        evs = parse_uart_log(u, position_tag=pos, flow_mlh=50.0)
        if not evs:
            print(f"  empty {tag}"); continue
        # Recompute V_true from scale file (don't trust the README value)
        if s.exists():
            g = pair_with_gravimetric(evs, s)
            V_t = g["V_true_per_drop_uL"]
        else:
            V_t = V_true
        pos_truth.setdefault(pos, []).append((V_t, len(evs)))
        for ev in evs:
            v = velocity_mmps(ev)
            if ev.transit_us < 500 or v < 50 or ev.pulse_top_us < 100 or ev.pulse_bot_us < 100:
                continue
            cm = chord_min(ev)
            V = V_pure(ev)
            rows.append(dict(
                tag=tag, position=pos, V_true=V_t,
                v_mmps=v, pulse_top_us=ev.pulse_top_us, pulse_bot_us=ev.pulse_bot_us,
                chord_min_mm=cm, V_pure_uL=V,
            ))
    df = pd.DataFrame(rows)
    weighted_truth = {}
    for pos, vals in pos_truth.items():
        ws = np.array([n for _, n in vals], dtype=float)
        vs = np.array([v for v, _ in vals], dtype=float)
        weighted_truth[pos] = float(np.sum(vs * ws) / np.sum(ws))
    return df, weighted_truth


def main():
    print("=== Pure physics: V = pi/6 * chord_min^3, NO K, NO regression ===\n")

    print("Yesterday standard-threshold runs:")
    df_y, truth_y = collect(STANDARD, YEST)
    print(f"  {len(df_y)} drops across {df_y['position'].nunique()} positions")

    print("\nToday's captures:")
    today_runs = [("p3_minus4mm_run01", "P3_today_minus4mm", 49.73)]
    # P1 redo (if present)
    if (TODAY / "p1_high_run02.uart.log").exists() and (TODAY / "p1_high_run02_scale.csv").exists():
        today_runs.append(("p1_high_run02", "P1_today_canonical_high", float("nan")))
    df_today, truth_today = collect(today_runs, TODAY)
    print(f"  {len(df_today)} drops across {df_today['position'].nunique()} positions")

    df = pd.concat([df_y, df_today], ignore_index=True)
    truth = {**truth_y, **truth_today}

    print("\nPer-position summary:")
    print(f"{'position':30s}  {'n':>4s}  {'V_true':>7s}  {'chord_min':>10s}  {'V_pure':>8s}  {'err %':>7s}")
    rows = []
    for pos in df["position"].unique():
        sub = df[df["position"] == pos]
        cm = sub["chord_min_mm"].mean()
        cm_std = sub["chord_min_mm"].std()
        Vp = sub["V_pure_uL"].mean()
        Vp_std = sub["V_pure_uL"].std()
        Vt = truth[pos]
        err = 100 * (Vp - Vt) / Vt
        print(f"{pos:30s}  {len(sub):>4d}  {Vt:>7.2f}  {cm:>6.2f}±{cm_std:.2f}  {Vp:>5.1f}±{Vp_std:.1f}  {err:+6.1f}%")
        rows.append((pos, len(sub), Vt, cm, cm_std, Vp, Vp_std, err))

    # ===== Figure: pure-physics K-fit landscape =====
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    pos_names = [r[0] for r in rows]
    errs = [r[7] for r in rows]
    colors = ["#27ae60" if abs(e) <= 5 else "#f39c12" if abs(e) <= 15 else "#c0392b" for e in errs]
    ax.bar(pos_names, errs, color=colors, alpha=0.9)
    ax.axhline(0, color="k", linewidth=0.8)
    ax.fill_between([-0.5, len(pos_names)-0.5], -5, 5, color="grey", alpha=0.18, label="±5 %")
    ax.fill_between([-0.5, len(pos_names)-0.5], -15, 15, color="grey", alpha=0.08, label="±15 %")
    ax.set_xticks(range(len(pos_names)))
    ax.set_xticklabels(pos_names, rotation=18, ha="right")
    ax.set_ylabel("err %  (V_pure − V_true) / V_true")
    ax.set_title("Pure physics V = π/6 · chord_min³  (no K, no regression)\n"
                 "Standard-threshold firmware runs only")
    ax.set_xlim(-0.5, len(pos_names)-0.5)
    ax.legend(loc="best", fontsize=8)
    for i, e in enumerate(errs):
        ax.text(i, e + (3 if e >= 0 else -5), f"{e:+.1f}%", ha="center", fontsize=9, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "fig8_pure_physics_chord_min_cubed.png", dpi=140)
    plt.close(fig)

    # Per-drop scatter
    fig, ax = plt.subplots(figsize=(7, 5))
    pos_order = list(df["position"].unique())
    palette = plt.cm.tab10(np.linspace(0, 1, len(pos_order)))
    for pos, c in zip(pos_order, palette):
        m = df["position"] == pos
        Vt = truth[pos]
        ax.scatter(np.repeat(Vt, m.sum()) + np.random.uniform(-0.4, 0.4, m.sum()),
                   df.loc[m, "V_pure_uL"], color=c, s=24, alpha=0.6, label=pos)
    lo, hi = 20, 90
    ax.plot([lo, hi], [lo, hi], "k:", linewidth=0.9, label="ideal")
    ax.fill_between([lo, hi], [lo*0.85, hi*0.85], [lo*1.15, hi*1.15], color="grey", alpha=0.12, label="±15 %")
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi*1.6)
    ax.set_xlabel("V_true (gravimetric, µL/drop)"); ax.set_ylabel("V_pure per drop (µL)")
    ax.set_title("Per-drop V_pure  (π/6 · chord_min³)  vs gravimetric truth")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(OUT / "fig9_pure_physics_per_drop.png", dpi=140)
    plt.close(fig)

    print(f"\nFigures: {OUT}/fig8_*.png  fig9_*.png")


if __name__ == "__main__":
    main()
