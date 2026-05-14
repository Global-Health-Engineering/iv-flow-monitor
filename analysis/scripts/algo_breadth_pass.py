"""Phase 2 breadth-pass orchestrator.

Given a manifest of (uart_log, scale_csv, position_tag, flow_mlh) tuples,
parse each capture, pair with gravimetric truth, run each algorithm
across all events, and tabulate K-fit per position + K_max/K_min.

For the 2026-05-13 dataset (edge-time only), only algo_reference and
F4 are exercisable — A1/B1/C1/E1/F1 require the raw waveform that
the 2026-05-14 PM ENABLE_RAW_CAPTURE firmware emits.

Usage:
    python algo_breadth_pass.py --yesterday    # runs the 2026-05-13 manifest
    python algo_breadth_pass.py --today        # runs today's captures (when ready)
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Imports from sibling modules
sys.path.insert(0, str(Path(__file__).parent))
from algo_replay import (
    DropEvent, AlgoResult, parse_uart_log, pair_with_gravimetric,
    algo_reference, evaluate,
)
from algos import f4_pulse_outlier


REPO_ROOT = Path(__file__).resolve().parents[2]


# 2026-05-13 PM run manifest. position_tag values come from
# data/raw/2026-05-13_pm_position_drift/README.md §17 mapping.
# Runs that failed at the bench (iter5_pos2: 0 drops captured) are omitted.
YESTERDAY_MANIFEST = [
    # (tag, uart_log, scale_csv, position_tag, flow_mlh)
    ("baseline_k127",        "baseline_k127",        "low_post_overnight",   50.0),
    ("iter1_k041",           "iter1_k041",           "low_post_overnight",   50.0),
    ("iter2_k0566",          "iter2_k0566",          "low_post_overnight",   50.0),
    ("iter2_confirm",        "iter2_confirm",        "low_post_overnight",   50.0),
    ("iter3_repos_k0283",    "iter3_repos_k0283",    "new_remount",          50.0),
    ("iter5_bot_core_only",  "iter5_bot_core_only",  "low_bot_core",         50.0),
    ("iter5b_top_low_highpos","iter5b_top_low_highpos","high_splash",        50.0),
    ("iter5b_pos3_top_low",  "iter5b_pos3_top_low",  "mid_low_remount",      50.0),
    ("iter7_hybrid_pos3",    "iter7_hybrid_pos3",    "mid_low_remount",      50.0),
    ("iter7b_stable",        "iter7b_stable",        "mid_low_remount",      40.0),  # README notes drip rate slowed
]


def load_manifest(manifest, data_root: Path) -> tuple[list[DropEvent], dict[str, float]]:
    """Load all runs in the manifest into a single list of events,
    with per-position V_true means (over all runs at that position).
    """
    all_events: list[DropEvent] = []
    per_position_truth: dict[str, list[float]] = {}

    for tag, base, position_tag, flow_mlh in manifest:
        uart_path = data_root / f"{base}_uart.log"
        scale_path = data_root / f"{base}_scale.csv"
        if not uart_path.exists():
            print(f"  WARN: missing {uart_path}")
            continue
        events = parse_uart_log(uart_path, position_tag=position_tag, flow_mlh=flow_mlh)
        if not events:
            print(f"  WARN: {tag} parsed 0 events")
            continue

        if scale_path.exists():
            grav = pair_with_gravimetric(events, scale_path)
            V_true = grav["V_true_per_drop_uL"]
            per_position_truth.setdefault(position_tag, []).append(V_true)
            print(f"  {tag:30s}: {len(events):3d} drops, V_true={V_true:.2f} µL/drop ({position_tag})")
        else:
            print(f"  {tag:30s}: {len(events):3d} drops, no scale (skipping V_true)")
        all_events.extend(events)

    V_true_per_position = {
        pos: float(np.mean(vals)) for pos, vals in per_position_truth.items()
    }
    return all_events, V_true_per_position


def run_breadth_pass(events: list[DropEvent], V_true_per_position: dict[str, float]) -> pd.DataFrame:
    """Run each algorithm over `events`, return a summary table."""
    rows = []

    # 0. Reference (current firmware math).
    metrics = evaluate(algo_reference, events, V_true_per_position)
    rows.append({
        "exp": 0, "family": "—", "algorithm": "algo_reference (firmware K=1.27)",
        "K_min": metrics["K_min"], "K_max": metrics["K_max"],
        "K_ratio": metrics["K_ratio"], "rejected_pct": metrics["rejected_pct"],
        "n_positions": len(metrics["per_position"]),
    })
    print(f"  exp0 algo_reference: K_min={metrics['K_min']:.3f} K_max={metrics['K_max']:.3f} ratio={metrics['K_ratio']:.2f}")

    # F4 — pulse outlier rejection. Needs a homogeneous population to fit
    # the τ(v) trend; we fit per position to avoid mixing populations.
    mask = np.ones(len(events), dtype=bool)
    for pos in V_true_per_position.keys():
        pos_events = [e for e in events if e.position_tag == pos]
        if not pos_events:
            continue
        pos_mask = f4_pulse_outlier.fit_rejection_mask(pos_events)
        pos_indices = [i for i, e in enumerate(events) if e.position_tag == pos]
        for j, keep in zip(pos_indices, pos_mask):
            mask[j] = keep

    algo_f4 = f4_pulse_outlier.make_algo(mask)
    metrics = evaluate(algo_f4, events, V_true_per_position)
    rows.append({
        "exp": 4, "family": "F", "algorithm": "F4 pulse-duration outlier rejection",
        "K_min": metrics["K_min"], "K_max": metrics["K_max"],
        "K_ratio": metrics["K_ratio"], "rejected_pct": metrics["rejected_pct"],
        "n_positions": len(metrics["per_position"]),
    })
    print(f"  exp4 F4 outlier-reject: K_min={metrics['K_min']:.3f} K_max={metrics['K_max']:.3f} ratio={metrics['K_ratio']:.2f} rejected={metrics['rejected_pct']:.1f}%")

    # Algorithms requiring raw waveform — flagged as 'pending raw data' until
    # the 2026-05-14 PM bench captures arrive.
    raw_required = [
        (1, "A", "A1 peak-relative threshold"),
        (2, "B", "B1 attenuation integral"),
        (3, "C", "C1 multi-feature regression"),
        (5, "E", "E1 oscillation-phase chord"),
        (6, "F", "F1 tail-energy asymmetry filter"),
    ]
    for exp, family, name in raw_required:
        rows.append({
            "exp": exp, "family": family, "algorithm": name,
            "K_min": float("nan"), "K_max": float("nan"),
            "K_ratio": float("nan"), "rejected_pct": float("nan"),
            "n_positions": 0,
        })

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yesterday", action="store_true",
                        help="Run against 2026-05-13 PM dataset (baseline + F4 only)")
    parser.add_argument("--today", action="store_true",
                        help="Run against 2026-05-14 PM dataset (all algorithms)")
    parser.add_argument("--out", type=Path,
                        default=REPO_ROOT / "analysis" / "figs" / "2026-05-14_pm" / "breadth_pass.csv",
                        help="Output CSV path")
    args = parser.parse_args()

    if args.yesterday and args.today:
        sys.exit("Pick one: --yesterday or --today")
    if not args.yesterday and not args.today:
        sys.exit("Pick one: --yesterday or --today")

    if args.yesterday:
        data_root = REPO_ROOT / "data" / "raw" / "2026-05-13_pm_position_drift"
        manifest = YESTERDAY_MANIFEST
    else:
        data_root = REPO_ROOT / "data" / "raw" / "2026-05-14_pm"
        # Today's manifest will be populated as captures land.
        manifest = []
        sys.exit("Today's manifest not populated yet — fill in algo_breadth_pass.py:TODAY_MANIFEST first.")

    print(f"Loading from {data_root}")
    events, V_true_per_position = load_manifest(manifest, data_root)
    print(f"Total events: {len(events)}")
    print(f"V_true per position: {V_true_per_position}")
    print()
    print("Running breadth pass:")
    summary = run_breadth_pass(events, V_true_per_position)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.out, index=False)
    print()
    print(f"Summary written to {args.out}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
