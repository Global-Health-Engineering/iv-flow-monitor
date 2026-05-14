"""Pulse-ratio landscape across mount positions, 2026-05-13 PM dataset.

§17 of docs/limitations.md quantifies position-dependence partly through
the BOT/TOP pulse-low ratio: ~0.92 (gravity-expected) at intermediate
mounts, jumping to ~2.3 at high-splash positions and ~7.8 when the BOT
low-threshold is lowered enough to catch the splash tail.

This script computes the per-drop pulse_bot_us / pulse_top_us ratio
across yesterday's 151 drops, plots the per-position distributions,
and tests whether the position labels are separable on this feature
alone. If they ARE, contamination-rejection (F-family) algorithms have
a working feature even on edge-time data; if NOT, raw shape features
are the only way forward.

Output: analysis/figs/2026-05-14_pm/pulse_ratio_per_position.png + CSV.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from algo_breadth_pass import YESTERDAY_MANIFEST, load_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data" / "raw" / "2026-05-13_pm_position_drift"
OUT_DIR = REPO_ROOT / "analysis" / "figs" / "2026-05-14_pm"


def main():
    events, V_true_per_position = load_manifest(YESTERDAY_MANIFEST, DATA_ROOT)
    rows = []
    for ev in events:
        if ev.pulse_top_us <= 0 or ev.pulse_bot_us <= 0:
            continue
        rows.append({
            "drop_n": ev.drop_n,
            "position_tag": ev.position_tag,
            "pulse_top_us": ev.pulse_top_us,
            "pulse_bot_us": ev.pulse_bot_us,
            "bot_top_ratio": ev.pulse_bot_us / ev.pulse_top_us,
            "transit_us": ev.transit_us,
            "top_raw_at_in": ev.top_raw_at_in,
            "bot_raw_at_in": ev.bot_raw_at_in,
        })
    df = pd.DataFrame(rows)
    print(f"Loaded {len(df)} drops across {df['position_tag'].nunique()} positions")

    # Per-position summary
    summary = df.groupby("position_tag").agg(
        n=("drop_n", "count"),
        pulse_top_mean=("pulse_top_us", "mean"),
        pulse_top_std=("pulse_top_us", "std"),
        pulse_bot_mean=("pulse_bot_us", "mean"),
        pulse_bot_std=("pulse_bot_us", "std"),
        bot_top_ratio_mean=("bot_top_ratio", "mean"),
        bot_top_ratio_std=("bot_top_ratio", "std"),
        top_raw_mean=("top_raw_at_in", "mean"),
        bot_raw_mean=("bot_raw_at_in", "mean"),
    ).round(2)
    print("\nPer-position pulse statistics (2026-05-13 PM):")
    print(summary.to_string())

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_DIR / "pulse_ratio_per_position.csv")
    print(f"\nWrote {OUT_DIR / 'pulse_ratio_per_position.csv'}")

    # Figure: 3-panel
    #   panel 1: pulse_top vs pulse_bot scatter colored by position
    #   panel 2: BOT/TOP ratio histogram per position
    #   panel 3: pulse_top distribution per position (umbilical = TOP_low extended)
    positions = sorted(df["position_tag"].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, max(len(positions), 1)))
    color_map = dict(zip(positions, colors))

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    ax1, ax2, ax3 = axes

    for pos in positions:
        sub = df[df["position_tag"] == pos]
        ax1.scatter(sub["pulse_top_us"] / 1000.0, sub["pulse_bot_us"] / 1000.0,
                    c=[color_map[pos]], s=40, alpha=0.7, label=f"{pos} (n={len(sub)})",
                    edgecolors="black", linewidths=0.4)
    # Gravity-expected: pulse_bot ≈ 0.92 * pulse_top (per §17)
    lim_max = df[["pulse_top_us", "pulse_bot_us"]].max().max() / 1000.0 * 1.1
    ax1.plot([0, lim_max], [0, lim_max], "g--", alpha=0.4, label="BOT/TOP = 1 (equal)")
    ax1.plot([0, lim_max], [0, lim_max * 0.92], "y:", alpha=0.5, label="BOT/TOP = 0.92 (gravity-expected)")
    ax1.set_xlabel("pulse_TOP_low (ms)")
    ax1.set_ylabel("pulse_BOT_low (ms)")
    ax1.set_title("Per-drop TOP vs BOT pulse durations, by position")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.grid(alpha=0.3)
    ax1.set_xlim(0, lim_max)
    ax1.set_ylim(0, lim_max)

    # BOT/TOP ratio histograms
    for pos in positions:
        sub = df[df["position_tag"] == pos]
        ax2.hist(sub["bot_top_ratio"], bins=20, alpha=0.6, color=color_map[pos],
                 label=f"{pos} (μ={sub['bot_top_ratio'].mean():.2f})")
    ax2.axvline(0.92, color="green", linestyle="--", alpha=0.5, label="gravity-expected 0.92")
    ax2.axvline(2.3, color="red", linestyle="--", alpha=0.5, label="§17 splash threshold ~2.3")
    ax2.set_xlabel("pulse_BOT / pulse_TOP ratio")
    ax2.set_ylabel("count")
    ax2.set_title("BOT/TOP ratio distribution per position")
    ax2.legend(loc="best", fontsize=8)
    ax2.grid(alpha=0.3)

    # pulse_top distribution per position (umbilical indicator)
    for pos in positions:
        sub = df[df["position_tag"] == pos]
        ax3.hist(sub["pulse_top_us"] / 1000.0, bins=20, alpha=0.6, color=color_map[pos],
                 label=f"{pos} (μ={sub['pulse_top_us'].mean() / 1000.0:.2f} ms)")
    ax3.axvline(2.2, color="green", linestyle="--", alpha=0.5, label="§17 clean drop ~2.2 ms")
    ax3.axvline(6.2, color="red", linestyle="--", alpha=0.5, label="§17 umbilical-extended ~6.2 ms")
    ax3.set_xlabel("pulse_TOP_low (ms)")
    ax3.set_ylabel("count")
    ax3.set_title("TOP pulse distribution per position (umbilical signature)")
    ax3.legend(loc="best", fontsize=8)
    ax3.grid(alpha=0.3)

    fig.tight_layout()
    out_path = OUT_DIR / "pulse_ratio_per_position.png"
    fig.savefig(out_path, dpi=140)
    print(f"Wrote {out_path}")

    # Quick separability test: per-position-mean BOT/TOP ratios.
    print("\nBOT/TOP per-position means (sorted):")
    print(summary["bot_top_ratio_mean"].sort_values().to_string())
    ratio_min = summary["bot_top_ratio_mean"].min()
    ratio_max = summary["bot_top_ratio_mean"].max()
    print(f"\nBOT/TOP ratio range across positions: {ratio_min:.2f} -> {ratio_max:.2f} ({ratio_max / ratio_min:.2f}x spread)")

    # Same for TOP pulse (umbilical indicator)
    top_min = summary["pulse_top_mean"].min() / 1000.0
    top_max = summary["pulse_top_mean"].max() / 1000.0
    print(f"pulse_TOP_low across positions: {top_min:.2f} -> {top_max:.2f} ms ({top_max / top_min:.2f}x spread)")


if __name__ == "__main__":
    main()
