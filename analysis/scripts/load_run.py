"""Load and process a single validation run CSV.

A run CSV has one row per drop event with raw firmware measurements:

    abs_ms, drop_N, transit_us, pulse_top_us, pulse_bot_us, top_raw, bot_raw

This module derives per-drop physical quantities under the
sphere-drop assumption and the dual-beam velocity model:

    velocity  = beam_separation_m / transit_us         (m / us)
    diameter  = mean(pulse_top, pulse_bot) * velocity  (m)
    volume_uL = (pi / 6) * diameter_m**3 * 1e9         (uL = mm^3)

Returns a pandas DataFrame ready for downstream aggregation.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


def load_run(csv_path: str | Path, beam_separation_mm: float) -> pd.DataFrame:
    """Load a single run CSV and add per-drop derived columns.

    Parameters
    ----------
    csv_path
        Path to a run CSV (e.g. data/raw/2026-05-13_macro20_50mlh_trial1_board1.csv).
    beam_separation_mm
        Measured TOP-to-BOT beam separation (from data/geometry.json,
        EXP-1 result). Drop velocity is inferred from this.

    Returns
    -------
    DataFrame with the seven raw columns plus three computed ones:
    velocity_m_s, drop_diameter_mm, drop_volume_uL.
    """
    df = pd.read_csv(csv_path)
    required = {"abs_ms", "drop_N", "transit_us", "pulse_top_us", "pulse_bot_us"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{csv_path}: missing columns {sorted(missing)}")

    beam_separation_m = beam_separation_mm / 1000.0
    transit_s = df["transit_us"] / 1e6
    df["velocity_m_s"] = beam_separation_m / transit_s

    pulse_mean_s = (df["pulse_top_us"] + df["pulse_bot_us"]) / 2.0 / 1e6
    df["drop_diameter_mm"] = (pulse_mean_s * df["velocity_m_s"]) * 1000.0

    diameter_m = df["drop_diameter_mm"] / 1000.0
    df["drop_volume_uL"] = (math.pi / 6.0) * diameter_m**3 * 1e9  # m^3 -> uL = mm^3

    return df


def summarise_run(df: pd.DataFrame, duration_s: float) -> dict[str, float]:
    """Reduce a per-drop DataFrame to one set of run-level numbers."""
    drop_count = len(df)
    total_volume_uL = float(df["drop_volume_uL"].sum())
    flow_rate_mlh = (total_volume_uL / 1000.0) / (duration_s / 3600.0)
    return {
        "drop_count": drop_count,
        "total_volume_uL": total_volume_uL,
        "device_flow_mlh": flow_rate_mlh,
        "mean_drop_volume_uL": total_volume_uL / drop_count if drop_count else float("nan"),
        "mean_velocity_m_s": float(df["velocity_m_s"].mean()),
        "transit_us_cv": float(df["transit_us"].std() / df["transit_us"].mean()),
    }
