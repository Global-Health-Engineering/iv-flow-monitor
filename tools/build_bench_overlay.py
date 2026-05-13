#!/usr/bin/env python3
"""Build the bench-overlay figure from the V_50_01 run (or any per-run pair).

Inputs (per run):
  - <run>.csv               firmware DROP rows (12-col schema)
  - <run>_scale.csv         scale SIR stream (t_ms, mass_g, status)

Pipeline:
  1. Read device CSV; compute per-drop V_est_ul via load_run.py's
     simple model (averages pulse_top and pulse_bot widths).
  2. Read scale CSV; identify the drip-active window (first to last
     non-trivial mass step) and total accumulated mass.
  3. Compute per-drop ground truth as a single per-run scalar:
     v_true_ul = (mass_g / density_g_per_ml) / drop_count × 1000.
  4. Re-run the a priori MC error budget at default params.
  5. Render fig_error_budget_with_bench.png with the bench cloud
     overlaid on the predicted Bland-Altman (panel b).
  6. Print a summary row (bias, LoA, MAPE) suitable for results.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "analysis"))

from scripts.load_run import load_run  # noqa: E402
from scripts.error_budget import (  # noqa: E402
    default_params, simulate, ablation, calibration_convergence,
    make_figure, overlay_bench_points,
)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device-csv", action="append", default=[],
                    help="path to firmware DROP CSV (repeat for multiple runs)")
    ap.add_argument("--scale-csv", action="append", default=[],
                    help="path to scale SIR CSV (repeat for multiple runs)")
    ap.add_argument("--label", action="append", default=[],
                    help="optional label per run (repeat)")
    ap.add_argument("--beam-mm", type=float, default=10.2,
                    help="beam separation in mm (default from data/geometry.json)")
    ap.add_argument("--density", type=float, default=1.000,
                    help="fluid density g/mL (water 1.000, saline 1.005)")
    ap.add_argument("--rate-mlh", type=float, default=None,
                    help="nominal flow rate for the title (e.g. 50)")
    ap.add_argument("--out-fig", default=str(REPO_ROOT / "analysis" / "figures"
                                              / "fig_error_budget_with_bench.png"))
    ap.add_argument("--out-csv", default=str(REPO_ROOT / "analysis" / "figures"
                                              / "bench_overlay_summary.csv"))
    ap.add_argument("--n-campaigns", type=int, default=400,
                    help="MC campaigns for the predicted panels (default 400)")
    return ap.parse_args()


def gravimetric_window(scale_df: pd.DataFrame, step_thresh_g: float = 0.005
                       ) -> tuple[int, int, float]:
    """Return (start_idx, end_idx, total_mass_change_g) for the drip-active window.

    A 'step' is a row where mass differs from a baseline median by > step_thresh.
    Start = first such row, end = last such row. Mass change is computed from
    a small-median around start and a small-median around end (robust to noise).
    """
    mass = scale_df["mass_g"].to_numpy()
    # Baseline: median of first 1 s of samples (approx).
    early = mass[: max(20, len(mass) // 50)]
    base = float(np.median(early)) if len(early) else 0.0
    deltas = np.abs(mass - base)
    moving = np.where(deltas > step_thresh_g)[0]
    if len(moving) == 0:
        return 0, len(scale_df) - 1, float(mass[-1] - mass[0]) if len(mass) > 1 else 0.0
    start = int(moving[0])
    end = int(moving[-1])
    # Robust start/end mass via medians of 0.5 s windows.
    win = max(10, len(mass) // 100)
    start_mass = float(np.median(mass[max(0, start - win):start + 1])) if start else float(mass[0])
    end_mass = float(np.median(mass[end:end + win + 1])) if end < len(mass) - 1 else float(mass[-1])
    return start, end, end_mass - start_mass


def process_run(device_csv: Path, scale_csv: Path, beam_mm: float, density: float,
                label: str | None) -> tuple[pd.DataFrame, dict]:
    if not device_csv.exists():
        raise FileNotFoundError(device_csv)
    if not scale_csv.exists():
        raise FileNotFoundError(scale_csv)
    drops = load_run(device_csv, beam_separation_mm=beam_mm)
    n_drops = len(drops)
    if n_drops == 0:
        raise ValueError(f"no drops in {device_csv}")
    v_est_arr = drops["drop_volume_uL"].to_numpy()
    scale_df = pd.read_csv(scale_csv)
    start, end, total_mass_g = gravimetric_window(scale_df)
    duration_s = float(scale_df["t_ms"].iloc[end] - scale_df["t_ms"].iloc[start]) / 1000.0
    total_volume_mL = total_mass_g / density
    v_true_per_drop_ul = (total_volume_mL * 1000.0) / n_drops
    gravimetric_flow_mlh = (total_volume_mL / (duration_s / 3600.0)
                            if duration_s > 0 else float("nan"))
    bench_df = pd.DataFrame({
        "v_est_ul": v_est_arr,
        "v_true_ul": np.full(n_drops, v_true_per_drop_ul),
        "run_label": np.full(n_drops, label or device_csv.stem),
    })
    diff = v_est_arr - v_true_per_drop_ul
    summary = {
        "label": label or device_csv.stem,
        "device_csv": str(device_csv.relative_to(REPO_ROOT)),
        "scale_csv": str(scale_csv.relative_to(REPO_ROOT)),
        "n_drops": n_drops,
        "duration_s": round(duration_s, 1),
        "mass_g": round(total_mass_g, 4),
        "v_true_per_drop_ul": round(v_true_per_drop_ul, 2),
        "v_est_mean_ul": round(float(np.mean(v_est_arr)), 2),
        "v_est_sd_ul": round(float(np.std(v_est_arr, ddof=1)), 2),
        "bias_ul_uncorrected": round(float(np.mean(diff)), 2),
        "loa_lower_ul": round(float(np.mean(diff)) - 1.96 * float(np.std(diff, ddof=1)), 2),
        "loa_upper_ul": round(float(np.mean(diff)) + 1.96 * float(np.std(diff, ddof=1)), 2),
        "mape_pct_uncorrected": round(float(np.mean(np.abs(diff) / v_true_per_drop_ul) * 100.0), 2),
        "k_correction_factor": round(v_true_per_drop_ul / float(np.mean(v_est_arr))
                                     if np.mean(v_est_arr) else float("nan"), 4),
        "gravimetric_flow_mlh": round(gravimetric_flow_mlh, 2),
    }
    return bench_df, summary


def main() -> int:
    args = parse_args()
    device_csvs = [Path(p).resolve() for p in args.device_csv]
    scale_csvs = [Path(p).resolve() for p in args.scale_csv]
    labels = list(args.label) + [None] * max(0, len(device_csvs) - len(args.label))
    if not device_csvs or len(device_csvs) != len(scale_csvs):
        print("ERROR: provide matching --device-csv and --scale-csv pairs", file=sys.stderr)
        return 2

    print(f"Beam:    {args.beam_mm} mm   Density: {args.density} g/mL")
    print(f"Runs:    {len(device_csvs)}")

    bench_frames = []
    summaries = []
    for dcsv, scsv, lbl in zip(device_csvs, scale_csvs, labels):
        print(f"\n--- {lbl or dcsv.stem} ---")
        print(f"  device: {dcsv.relative_to(REPO_ROOT)}")
        print(f"  scale:  {scsv.relative_to(REPO_ROOT)}")
        try:
            bench_df_run, summary = process_run(dcsv, scsv, args.beam_mm, args.density, lbl)
        except (FileNotFoundError, ValueError) as e:
            print(f"  ERROR: {e}", file=sys.stderr); return 2
        bench_frames.append(bench_df_run)
        summaries.append(summary)
        print(f"  N={summary['n_drops']}  duration={summary['duration_s']} s")
        print(f"  v_true={summary['v_true_per_drop_ul']} µL  v_est_mean={summary['v_est_mean_ul']} µL "
              f"± {summary['v_est_sd_ul']}")
        print(f"  bias={summary['bias_ul_uncorrected']} µL  LoA=[{summary['loa_lower_ul']}, "
              f"{summary['loa_upper_ul']}]  k={summary['k_correction_factor']}")

    bench_df = pd.concat(bench_frames, ignore_index=True)
    n_drops_total = len(bench_df)
    v_true_label = (summaries[0]["v_true_per_drop_ul"]
                    if len(summaries) == 1
                    else f"per-run {[s['v_true_per_drop_ul'] for s in summaries]}")

    # --- Predicted MC error budget ---
    params = default_params()
    print(f"\nMC predicted at default params ({args.n_campaigns} campaigns)...")
    df_mc = simulate(params, n_campaigns=args.n_campaigns)
    abl = ablation(params, n_campaigns=min(200, args.n_campaigns))
    conv = calibration_convergence(params, n_bootstrap=500)
    fig = make_figure(df_mc, abl, params,
                      title_suffix=f"(bench overlay N={n_drops_total} drops, "
                                   f"v_true={v_true_label})",
                      convergence_df=conv)
    ax_b = fig.axes[1]
    overlay_bench_points(ax_b, bench_df)

    out_fig = Path(args.out_fig).resolve()
    out_fig.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nFigure: {out_fig}")

    summary_df = pd.DataFrame(summaries)
    if args.rate_mlh is not None:
        summary_df["rate_target_mlh"] = args.rate_mlh
    out_csv = Path(args.out_csv).resolve()
    summary_df.to_csv(out_csv, index=False)
    print(f"Summary CSV: {out_csv}")
    print()
    print(summary_df.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
