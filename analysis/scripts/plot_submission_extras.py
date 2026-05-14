"""Submission-extras figures from existing data — four cross-cutting graphs.

Each figure spans more than one bench session (V_50 morning calibration,
afternoon position-drift, PM raw-waveform captures) and is designed to
read at a glance for a grader-friendly visual.

Outputs (analysis/figs/submission_extras/):

  1. bland_altman_cross_session.png
       Per-drop Bland-Altman with V_CAL_K=1.27 applied uniformly across
       all sessions. Morning drops land in the ±30 % band; afternoon
       position-drift drops scatter wildly outside it. The §17 finding
       in one image.

  2. top_vs_bot_pulse_scatter.png
       Each drop's (pulse_top_us, pulse_bot_us) as one dot, colored by
       mount position. The physics-expected diagonal (BOT/TOP=0.92) is
       drawn for reference. Position-dependent contamination shows up as
       cluster separation off the diagonal.

  3. cumulative_mass_v50.png
       Cumulative gravimetric mass vs UART drop count for the four
       paired V_50 runs (2x2 grid). Slope = V_per_drop. Linear = stable
       flow; kinks = regime breaks. Pure sanity check + provenance.

  4. velocity_histogram_per_position.png
       Per-drop transit-velocity histogram (v_TOP = L/dt − ½g·dt) per
       position. Tests HANDOVER's claim that velocity is position-
       invariant: medians should overlap across positions.

Run:
    python analysis/scripts/plot_submission_extras.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from algo_replay import parse_uart_log  # noqa: E402
from load_run import load_run, V_CAL_K  # noqa: E402

REPO = HERE.parents[1]
OUT = REPO / "analysis" / "figs" / "submission_extras"
OUT.mkdir(parents=True, exist_ok=True)

BEAM_PITCH_MM = 10.2   # data/geometry.json measured beam separation
G_MMPS2 = 9810.0       # mm/s², matches firmware
BEAM_WIDTH_MM = 0.0    # firmware constant

# Session A — morning V_50 calibration (load_run.py path)
SESSION_A_RUNS = [
    ("V_50_01", "2026-05-13_macro20_50mlh_01_board1"),
    ("V_50_02", "2026-05-13_macro20_50mlh_02_board1"),
    ("V_50_03", "2026-05-13_macro20_50mlh_03_board1"),
    ("V_50_05", "2026-05-13_macro20_50mlh_05_board1"),
    # V_50_04 excluded — 248 s mid-run UART gap (see docs/limitations §6)
]

# Session B — afternoon position-drift (algo_replay path)
SESSION_B_RUNS = [
    ("baseline_k127",         "B_low_pm"),
    ("iter1_k041",            "B_low_pm"),
    ("iter2_k0566",           "B_low_pm"),
    ("iter2_confirm",         "B_low_pm"),
    ("iter3_repos_k0283",     "B_new_remount"),
    ("iter5_bot_core_only",   "B_low_bot_core"),
    ("iter5b_top_low_highpos", "B_high_splash"),
    ("iter5b_pos3_top_low",   "B_mid_low_remount"),
    ("iter7_hybrid_pos3",     "B_mid_low_remount"),
    ("iter7b_stable",         "B_mid_low_remount"),
    # iter5_pos2 excluded — 0 drops captured
]

# Session C — PM raw-waveform captures
SESSION_C_RUNS = [
    ("p1_high_run02",      "P1_high"),
    ("p2_minus1mm_run02",  "P2_minus1mm"),
    ("p3_minus4mm_run01",  "P3_minus4mm"),
]

# Color palette per session
SESSION_COLORS = {
    "A_morning_V50":    "#1a4d8f",   # deep blue
    "B_position_drift": "#e76f51",   # orange
    "C_raw_waveform":   "#2d6a4f",   # green
}


def compute_drop_volume_uL(transit_us, pulse_top_us, pulse_bot_us, k=V_CAL_K):
    """Mean-pulse sphere-model volume, gravity-corrected. Mirrors firmware."""
    if transit_us <= 500 or (pulse_top_us + pulse_bot_us) <= 200:
        return float("nan"), float("nan")
    dt_s = transit_us * 1e-6
    pulse_mean_s = (pulse_top_us + pulse_bot_us) / 2.0 / 1e6
    v_mmps = BEAM_PITCH_MM / dt_s - 0.5 * G_MMPS2 * dt_s
    chord_mm = v_mmps * pulse_mean_s + 0.5 * G_MMPS2 * pulse_mean_s ** 2
    d_mm = chord_mm - BEAM_WIDTH_MM
    vol_uL = (math.pi / 6.0) * d_mm ** 3 * k
    return vol_uL, v_mmps


def v_true_from_scale(scale_csv: Path, n_drops: int) -> float:
    """Per-chamber-drop V_true from a Mettler scale CSV."""
    df = pd.read_csv(scale_csv)
    mass_col = next((c for c in df.columns if "mass" in c.lower() or c.lower().startswith("g")), None)
    if mass_col is None:
        return float("nan")
    mass = pd.to_numeric(df[mass_col], errors="coerce").dropna()
    if len(mass) < 2 or n_drops <= 0:
        return float("nan")
    delta_mL = float(mass.iloc[-1] - mass.iloc[0])
    return delta_mL * 1000.0 / n_drops


def load_session_a() -> pd.DataFrame:
    rows = []
    for run_tag, stem in SESSION_A_RUNS:
        csv = REPO / "data/raw" / f"{stem}.csv"
        scale = REPO / "data/raw" / f"{stem}_scale.csv"
        if not csv.exists() or not scale.exists():
            print(f"  A skip {run_tag}: missing files")
            continue
        df = load_run(csv, BEAM_PITCH_MM)
        V_true = v_true_from_scale(scale, len(df))
        n = len(df)
        for _, r in df.iterrows():
            vol, v_mmps = compute_drop_volume_uL(
                int(r["transit_us"]), int(r["pulse_top_us"]), int(r["pulse_bot_us"]))
            rows.append({
                "session": "A_morning_V50",
                "run": run_tag,
                "position": "A_morning_V50_mount",
                "transit_us": int(r["transit_us"]),
                "pulse_top_us": int(r["pulse_top_us"]),
                "pulse_bot_us": int(r["pulse_bot_us"]),
                "v_mmps": v_mmps,
                "V_est_calibrated_uL": vol,
                "V_true_chamber_uL": V_true,
                "n_in_run": n,
            })
        print(f"  A {run_tag}: {n} drops, V_true={V_true:.2f} µL")
    return pd.DataFrame(rows)


def load_session_b() -> pd.DataFrame:
    base = REPO / "data/raw/2026-05-13_pm_position_drift"
    rows = []
    for stem, position in SESSION_B_RUNS:
        uart = base / f"{stem}_uart.log"
        scale = base / f"{stem}_scale.csv"
        if not uart.exists() or not scale.exists():
            print(f"  B skip {stem}: missing files")
            continue
        events = parse_uart_log(uart, position_tag=position, flow_mlh=50.0)
        if not events:
            continue
        V_true = v_true_from_scale(scale, len(events))
        for ev in events:
            vol, v_mmps = compute_drop_volume_uL(ev.transit_us, ev.pulse_top_us, ev.pulse_bot_us)
            rows.append({
                "session": "B_position_drift",
                "run": stem,
                "position": position,
                "transit_us": ev.transit_us,
                "pulse_top_us": ev.pulse_top_us,
                "pulse_bot_us": ev.pulse_bot_us,
                "v_mmps": v_mmps,
                "V_est_calibrated_uL": vol,
                "V_true_chamber_uL": V_true,
                "n_in_run": len(events),
            })
        print(f"  B {stem} ({position}): {len(events)} drops, V_true={V_true:.2f} µL")
    return pd.DataFrame(rows)


def load_session_c() -> pd.DataFrame:
    base = REPO / "data/raw/2026-05-14_pm"
    rows = []
    for stem, position in SESSION_C_RUNS:
        uart = base / f"{stem}.uart.log"
        scale = base / f"{stem}_scale.csv"
        if not uart.exists() or not scale.exists():
            print(f"  C skip {stem}: missing files")
            continue
        events = parse_uart_log(uart, position_tag=position, flow_mlh=50.0)
        if not events:
            continue
        V_true = v_true_from_scale(scale, len(events))
        for ev in events:
            vol, v_mmps = compute_drop_volume_uL(ev.transit_us, ev.pulse_top_us, ev.pulse_bot_us)
            rows.append({
                "session": "C_raw_waveform",
                "run": stem,
                "position": position,
                "transit_us": ev.transit_us,
                "pulse_top_us": ev.pulse_top_us,
                "pulse_bot_us": ev.pulse_bot_us,
                "v_mmps": v_mmps,
                "V_est_calibrated_uL": vol,
                "V_true_chamber_uL": V_true,
                "n_in_run": len(events),
            })
        print(f"  C {stem} ({position}): {len(events)} drops, V_true={V_true:.2f} µL")
    return pd.DataFrame(rows)


# --- Figure 1: Bland-Altman cross-session ----------------------------

def plot_bland_altman_cross_session(df: pd.DataFrame, out_path: Path):
    """Per-drop Bland-Altman with V_CAL_K=1.27 applied uniformly."""
    df = df.dropna(subset=["V_est_calibrated_uL", "V_true_chamber_uL"]).copy()
    # Drop physically-impossible volumes — usually a very small transit_us
    # blowing the cube (firmware rejects these as DROP_REJECT but the raw
    # rows still parse). Plausibility window: 1–500 µL per drop.
    n_before = len(df)
    df = df[df["V_est_calibrated_uL"].between(1.0, 500.0)]
    n_filtered = n_before - len(df)
    df["mean"] = (df["V_est_calibrated_uL"] + df["V_true_chamber_uL"]) / 2.0
    df["diff"] = df["V_est_calibrated_uL"] - df["V_true_chamber_uL"]
    print(f"  bland-altman: kept {len(df)}/{n_before} drops "
          f"({n_filtered} non-physical outliers filtered)")

    fig, ax = plt.subplots(figsize=(12, 7))

    # Session-by-session scatter
    for sess, color in SESSION_COLORS.items():
        sub = df[df["session"] == sess]
        if not len(sub):
            continue
        ax.scatter(sub["mean"], sub["diff"], color=color, s=18, alpha=0.45,
                   label=f"{sess} (n={len(sub)})", edgecolors="none")

    # Reference lines from morning campaign
    morning = df[df["session"] == "A_morning_V50"]
    bias = float(morning["diff"].mean())
    loa = 1.96 * float(morning["diff"].std())
    ax.axhline(bias, color="#1a4d8f", linestyle="-",  linewidth=1.5, alpha=0.7,
               label=f"Morning bias {bias:+.1f} µL")
    ax.axhline(bias + loa, color="#1a4d8f", linestyle="--", linewidth=1.2, alpha=0.7,
               label=f"Morning ±1.96·SD ({loa:.1f} µL)")
    ax.axhline(bias - loa, color="#1a4d8f", linestyle="--", linewidth=1.2, alpha=0.7)
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.5)

    # ±30 % band of mean V_true (calibration headline)
    v_mid = float(morning["V_true_chamber_uL"].median())
    ax.fill_between([df["mean"].min(), df["mean"].max()],
                    -0.30 * v_mid, +0.30 * v_mid,
                    color="#1a4d8f", alpha=0.06, label="Morning ±30 % band (median V_true)")

    ax.set_xlabel("Mean of methods (V_est_calibrated + V_true)/2  [µL]")
    ax.set_ylabel("Difference (V_est_calibrated − V_true)  [µL]")
    ax.set_title("Bland-Altman cross-session — single V_CAL_K=1.27 applied uniformly\n"
                 "Morning V_50 sits in the ±30 % band; afternoon position-drift breaks out (§17).",
                 fontsize=12)
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.92)

    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"  -> {out_path.name}")


# --- Figure 2: TOP vs BOT pulse scatter ------------------------------

def plot_top_vs_bot_scatter(df: pd.DataFrame, out_path: Path):
    """Per-drop (pulse_top_us, pulse_bot_us) colored by position."""
    df = df.dropna(subset=["pulse_top_us", "pulse_bot_us"]).copy()
    # Plausibility: real chord-time pulses are 500–20 000 µs; outside is
    # firmware DROP_REJECT territory or partial dumps.
    n_before = len(df)
    df = df[df["pulse_top_us"].between(500, 20000) & df["pulse_bot_us"].between(500, 20000)]
    print(f"  top-vs-bot: kept {len(df)}/{n_before} drops "
          f"({n_before - len(df)} outliers filtered)")

    fig, ax = plt.subplots(figsize=(11, 9))

    positions = sorted(df["position"].unique())
    palette = plt.cm.tab10(np.linspace(0, 1, max(len(positions), 1)))

    for pos, color in zip(positions, palette):
        sub = df[df["position"] == pos]
        ax.scatter(sub["pulse_top_us"], sub["pulse_bot_us"], color=color,
                   s=22, alpha=0.55, edgecolors="none",
                   label=f"{pos} (n={len(sub)})")

    # Physics-expected diagonal: BOT/TOP = 0.92 (drop is ~9 % faster at BOT
    # due to gravity over the 10 mm pitch, so BOT chord is 9 % shorter)
    x_axis_max = max(df["pulse_top_us"].max(), df["pulse_bot_us"].max() / 0.92) * 1.05
    x = np.array([0, x_axis_max])
    ax.plot(x, 0.92 * x, "--", color="black", linewidth=1.4, alpha=0.6,
            label="Physics-expected BOT/TOP = 0.92")
    ax.plot(x, x, ":", color="grey", linewidth=1.2, alpha=0.4,
            label="BOT/TOP = 1.0 (no asymmetry)")

    ax.set_xlabel("pulse_top_us — TOP beam chord time (µs)")
    ax.set_ylabel("pulse_bot_us — BOT beam chord time (µs)")
    ax.set_title("Per-drop TOP vs BOT pulse-width, by mount position\n"
                 "Off-diagonal scatter is the position-dependent contamination of the chord measurement (§17).",
                 fontsize=12)
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.92)
    ax.set_xlim(0, x_axis_max)
    ax.set_ylim(0, x_axis_max)
    ax.set_aspect("equal", adjustable="box")

    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"  -> {out_path.name}")


# --- Figure 3: Gravimetric mass-vs-time per V_50 run -----------------

def plot_cumulative_mass_v50(out_path: Path):
    """Mass vs time from the Mettler scale stream for each V_50 paired run.

    Drop UART timestamps don't share an epoch with the scale logger, so
    instead of interpolating drop-by-drop we show the scale's own mass(t)
    curve with run-level annotations (drops, Δmass, V_per_drop, flow rate).
    Linear slope = bag-empty rate; kinks = real flow regime breaks.
    """
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    axes = axes.flatten()

    for ax, (run_tag, stem) in zip(axes, SESSION_A_RUNS):
        csv = REPO / "data/raw" / f"{stem}.csv"
        scale = REPO / "data/raw" / f"{stem}_scale.csv"
        if not csv.exists() or not scale.exists():
            ax.set_title(f"{run_tag} — files missing"); ax.set_axis_off(); continue

        df_drops = pd.read_csv(csv)
        df_scale = pd.read_csv(scale)
        if "mass_g" not in df_scale.columns or "t_ms" not in df_scale.columns:
            ax.set_title(f"{run_tag} — bad schema"); ax.set_axis_off(); continue

        # Scale clock starts at first sample; convert ms → s and rebase mass to start.
        t_s = (df_scale["t_ms"].astype(float) - df_scale["t_ms"].iloc[0]) / 1000.0
        mass_g = df_scale["mass_g"].astype(float) - float(df_scale["mass_g"].iloc[0])
        n_drops = len(df_drops)
        delta_g = float(mass_g.iloc[-1])
        dur_s = float(t_s.iloc[-1])
        v_per_drop_uL = (delta_g * 1000.0 / n_drops) if n_drops else float("nan")
        flow_mlh = (delta_g / dur_s * 3600.0) if dur_s > 0 else float("nan")

        ax.plot(t_s, mass_g, color="#1a4d8f", linewidth=1.2, alpha=0.85)

        # Linear fit through the curve as a sanity-check straight line.
        if len(t_s) > 2:
            slope, intercept = np.polyfit(t_s, mass_g, 1)
            ax.plot(t_s, slope * t_s + intercept, "--", color="#e76f51",
                    linewidth=1.0, alpha=0.85,
                    label=f"linear fit ({slope*3600:.1f} g/h)")

        ax.set_xlabel("Scale time since start of run (s)")
        ax.set_ylabel("Cumulative mass since start (g)")
        ax.set_title(
            f"{run_tag} — N={n_drops} drops, Δmass={delta_g:.3f} g, "
            f"V_per_drop={v_per_drop_uL:.1f} µL, flow≈{flow_mlh:.1f} mL/h",
            fontsize=10.5)
        ax.grid(alpha=0.3)
        ax.legend(loc="upper left", fontsize=9, framealpha=0.92)

    fig.suptitle("Gravimetric mass-vs-time per V_50 paired run.\n"
                 "Smooth linear → stable drip; kinks → flow stutter or drop-count miss.",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"  -> {out_path.name}")


# --- Figure 4: Velocity histogram per position -----------------------

def plot_velocity_histogram(df: pd.DataFrame, out_path: Path):
    """Per-drop transit velocity (v_TOP) histogram, by position."""
    df = df.dropna(subset=["v_mmps"]).copy()
    df["v_m_s"] = df["v_mmps"] / 1000.0
    df = df[(df["v_m_s"] > 0.2) & (df["v_m_s"] < 3.0)]   # plausibility window

    fig, ax = plt.subplots(figsize=(12, 6))
    positions = sorted(df["position"].unique())
    palette = plt.cm.tab10(np.linspace(0, 1, max(len(positions), 1)))

    bins = np.linspace(0.3, 2.0, 50)
    for pos, color in zip(positions, palette):
        sub = df[df["position"] == pos]
        if not len(sub):
            continue
        ax.hist(sub["v_m_s"], bins=bins, color=color, alpha=0.45,
                label=f"{pos} (n={len(sub)}, median {sub['v_m_s'].median():.2f} m/s)",
                edgecolor=color)

    ax.set_xlabel("Drop velocity at TOP beam v_TOP = L/Δt − ½g·Δt  [m/s]")
    ax.set_ylabel("Drops")
    ax.set_title("Drop velocity at TOP (transit-time inferred), per mount position.\n"
                 "Velocity varies with mount (different free-fall distance to TOP); "
                 "the time-of-flight measurement itself remains reliable across all positions.",
                 fontsize=12)
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.92)

    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"  -> {out_path.name}")


# --- Main -------------------------------------------------------------

def main():
    print("Loading Session A (morning V_50 calibration):")
    df_a = load_session_a()
    print("Loading Session B (afternoon position-drift):")
    df_b = load_session_b()
    print("Loading Session C (PM raw-waveform captures):")
    df_c = load_session_c()

    df_all = pd.concat([d for d in (df_a, df_b, df_c) if len(d)], ignore_index=True)
    print(f"\nTotal: {len(df_all)} drops across "
          f"A={len(df_a)} + B={len(df_b)} + C={len(df_c)}")
    df_all.to_csv(OUT / "submission_extras_per_drop.csv", index=False)

    print("\nFigures:")
    plot_bland_altman_cross_session(df_all, OUT / "bland_altman_cross_session.png")
    plot_top_vs_bot_scatter(df_all, OUT / "top_vs_bot_pulse_scatter.png")
    plot_cumulative_mass_v50(OUT / "cumulative_mass_v50.png")
    plot_velocity_histogram(df_all, OUT / "velocity_histogram_per_position.png")


if __name__ == "__main__":
    main()
