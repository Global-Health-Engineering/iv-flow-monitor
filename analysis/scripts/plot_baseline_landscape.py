"""Plot the K-fit landscape across positions from yesterday's edge-time data.

Generates analysis/figs/2026-05-14_pm/baseline_K_per_position.png — the
"before raw waveforms" snapshot that today's bench session is supposed
to improve on (or document as architecturally bounded per §17).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from algo_replay import parse_uart_log, pair_with_gravimetric, algo_reference, evaluate
from algos import f4_pulse_outlier
from algo_breadth_pass import YESTERDAY_MANIFEST, load_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data" / "raw" / "2026-05-13_pm_position_drift"
OUT_DIR = REPO_ROOT / "analysis" / "figs" / "2026-05-14_pm"


def main():
    events, V_true_per_position = load_manifest(YESTERDAY_MANIFEST, DATA_ROOT)
    print(f"Loaded {len(events)} events across {len(V_true_per_position)} positions.")

    # Per-position K under canonical firmware math.
    ref_metrics = evaluate(algo_reference, events, V_true_per_position)
    per_pos = ref_metrics["per_position"].copy()

    # F4 mask per position (so the rejection is fit on homogeneous data).
    mask = np.ones(len(events), dtype=bool)
    for pos in V_true_per_position.keys():
        pos_events = [e for e in events if e.position_tag == pos]
        if not pos_events:
            continue
        pos_mask = f4_pulse_outlier.fit_rejection_mask(pos_events)
        pos_indices = [i for i, e in enumerate(events) if e.position_tag == pos]
        for j, keep in zip(pos_indices, pos_mask):
            mask[j] = keep
    f4_algo = f4_pulse_outlier.make_algo(mask)
    f4_metrics = evaluate(f4_algo, events, V_true_per_position)
    f4_per_pos = f4_metrics["per_position"].copy()

    # Build the figure.
    positions = per_pos["position_tag"].tolist()
    K_ref = per_pos["K_fit"].tolist()
    K_f4 = (
        f4_per_pos.set_index("position_tag")
        .reindex(positions)["K_fit"].tolist()
    )

    fig, (ax_K, ax_V) = plt.subplots(1, 2, figsize=(12, 5))

    x = np.arange(len(positions))
    width = 0.38
    ax_K.bar(x - width / 2, K_ref, width, label="algo_reference (firmware K=1.27 mean-pulse)",
             color="steelblue")
    ax_K.bar(x + width / 2, K_f4, width, label="F4 + reference (pulse-outlier reject)",
             color="indianred")
    ax_K.axhline(1.0, color="green", linestyle="--", alpha=0.5, label="K=1.0 (ideal)")
    ax_K.axhline(1.27, color="orange", linestyle=":", alpha=0.5, label="K=1.27 (firmware ship)")
    ax_K.set_xticks(x)
    ax_K.set_xticklabels(positions, rotation=30, ha="right")
    ax_K.set_ylabel("K_fit = V_true / V_est")
    ax_K.set_title(
        f"Per-position K-fit, 2026-05-13 PM dataset\n"
        f"K_min={ref_metrics['K_min']:.3f}, K_max={ref_metrics['K_max']:.3f}, "
        f"ratio={ref_metrics['K_ratio']:.2f}× "
        f"(F4 rejected {f4_metrics['rejected_pct']:.1f}%)"
    )
    ax_K.legend(loc="best", fontsize=8)
    ax_K.grid(axis="y", alpha=0.3)

    # Side panel: V_true vs V_est_mean per position (the chord-time gap).
    V_true_vals = per_pos["V_true_uL"].tolist()
    V_est_vals = per_pos["V_est_mean_uL"].tolist()
    ax_V.scatter(V_true_vals, V_est_vals, c="steelblue", s=80, zorder=3)
    for v_t, v_e, pos in zip(V_true_vals, V_est_vals, positions):
        ax_V.annotate(pos, (v_t, v_e), fontsize=7, xytext=(5, 5), textcoords="offset points")
    lim = max(max(V_true_vals), max(V_est_vals)) * 1.1
    ax_V.plot([0, lim], [0, lim], color="green", linestyle="--", alpha=0.5, label="V_est = V_true")
    ax_V.plot([0, lim], [0, lim / 1.27], color="orange", linestyle=":", alpha=0.5,
              label="firmware K=1.27 (V_est = 1.27·V_true)")
    ax_V.set_xlabel("V_true_per_drop (µL) — gravimetric truth")
    ax_V.set_ylabel("V_est_per_drop (µL) — algo_reference output")
    ax_V.set_title("Chord-time estimate vs gravimetric truth, per position")
    ax_V.legend(loc="best", fontsize=8)
    ax_V.grid(alpha=0.3)
    ax_V.set_xlim(0, lim)
    ax_V.set_ylim(0, lim)

    fig.tight_layout()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "baseline_K_per_position.png"
    fig.savefig(out_path, dpi=140)
    print(f"Wrote {out_path}")

    # Also dump the per-position table as CSV for the notebook.
    csv_path = OUT_DIR / "baseline_K_per_position.csv"
    per_pos.to_csv(csv_path, index=False)
    print(f"Wrote {csv_path}")
    print()
    print(per_pos.to_string(index=False))


if __name__ == "__main__":
    main()
