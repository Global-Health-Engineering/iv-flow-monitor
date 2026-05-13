"""Load and process a single validation run CSV.

A run CSV has one row per drop event with raw firmware measurements:

    abs_ms, drop_N, transit_us, pulse_top_us, pulse_bot_us, ...

This module derives per-drop physical quantities under the sphere-drop
assumption using the same gravity-corrected chord physics the firmware
implements in main.c (so offline numbers match the device's on-LCD output
byte-for-byte):

    v_TOP   = L / dt   -   ½g · dt           (m/s, gravity-corrected)
    tau     = mean(pulse_TOP, pulse_BOT)     (s)
    chord   = v_TOP · tau  +  ½g · tau²      (m)
    d_mm    = chord_mm  -  BEAM_WIDTH_MM     (mm; BEAM_WIDTH=0 in Rev-B)
    V_uL    = (π/6) · d_mm³  ·  V_CAL_K      (µL)

The V_CAL_K scalar is the 2026-05-13 bench-fitted correction that absorbs
the residual chord-vs-volume gap from drop oscillation and TOP/BOT
asymmetry. See `docs/results.md` for the derivation.

Returns a pandas DataFrame ready for downstream aggregation.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

V_CAL_K = 1.27
"""Scalar correction applied to the chord-sphere drop volume.

Mirrors firmware/STM32CubeIDE/InfusionBA2/Core/Src/main.c (#define V_CAL_K).
Derived as the unweighted mean of per-run k = V_true_gravimetric / V_est
across the four 2026-05-13 campaigns. See docs/results.md for the
derivation and the residual-error breakdown."""

G_MPS2 = 9.81
"""Gravitational acceleration, m/s². Mirrors firmware G_MMPS2 / 1000."""

BEAM_WIDTH_MM = 0.0
"""Point-beam approximation. Mirrors firmware #define BEAM_WIDTH_MM."""


def load_run(csv_path: str | Path, beam_separation_mm: float) -> pd.DataFrame:
    """Load a single run CSV and add per-drop derived columns.

    Parameters
    ----------
    csv_path
        Path to a run CSV (e.g. data/raw/2026-05-13_macro20_50mlh_01_board1.csv).
    beam_separation_mm
        Measured TOP-to-BOT beam separation (from data/geometry.json,
        EXP-1 result). Drop velocity at TOP is inferred from this and
        the gravity correction (½g·dt) applied.

    Returns
    -------
    DataFrame with the raw columns plus three computed ones:
    velocity_m_s (gravity-corrected at TOP), drop_diameter_mm, drop_volume_uL.
    """
    df = pd.read_csv(csv_path)
    required = {"abs_ms", "drop_N", "transit_us", "pulse_top_us", "pulse_bot_us"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{csv_path}: missing columns {sorted(missing)}")

    beam_separation_m = beam_separation_mm / 1000.0
    transit_s = df["transit_us"] / 1e6
    df["velocity_m_s"] = beam_separation_m / transit_s - 0.5 * G_MPS2 * transit_s

    pulse_mean_s = (df["pulse_top_us"] + df["pulse_bot_us"]) / 2.0 / 1e6
    chord_m = df["velocity_m_s"] * pulse_mean_s + 0.5 * G_MPS2 * pulse_mean_s ** 2
    df["drop_diameter_mm"] = chord_m * 1000.0 - BEAM_WIDTH_MM

    diameter_m = df["drop_diameter_mm"] / 1000.0
    df["drop_volume_uL"] = (math.pi / 6.0) * diameter_m**3 * 1e9 * V_CAL_K  # m^3 -> uL

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
