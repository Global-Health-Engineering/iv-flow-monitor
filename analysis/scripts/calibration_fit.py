"""Fit a scalar correction factor k against gravimetric ground truth.

The sphere-drop volume model is an approximation. A single scalar k
absorbs systematic deviations (beam-width bias, sphere-model error,
fluid density, etc.) without overfitting:

    device_flow_corrected = k * device_flow_uncorrected

k is fit on a TRAIN split (least-squares against gravimetric truth)
and reported with TEST split out-of-sample error so overfitting to
a small dataset is visible.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DENSITY_G_PER_ML = 1.005  # Ringer's lactate, Lacy et al. 2009


def gravimetric_flow_mlh(mass_g: float, duration_s: float) -> float:
    """Convert mass and duration to true flow rate."""
    return (mass_g / DENSITY_G_PER_ML) / (duration_s / 3600.0)


def fit_correction_factor(
    train_df: pd.DataFrame,
    device_col: str = "device_flow_mlh",
    truth_col: str = "gravimetric_flow_mlh",
) -> float:
    """Fit scalar k by least-squares such that k * device ≈ truth.

    Closed form: k = sum(device * truth) / sum(device^2). Equivalent
    to OLS with no intercept, which is the right shape for a
    multiplicative correction.
    """
    device = train_df[device_col].to_numpy()
    truth = train_df[truth_col].to_numpy()
    if not np.all(np.isfinite(device)) or not np.all(np.isfinite(truth)):
        raise ValueError("non-finite values in train data")
    return float(np.sum(device * truth) / np.sum(device * device))


def apply_correction(df: pd.DataFrame, k: float, device_col: str = "device_flow_mlh") -> pd.DataFrame:
    """Return df with an added device_flow_corrected_mlh column."""
    out = df.copy()
    out["device_flow_corrected_mlh"] = k * out[device_col]
    return out


def stratified_split(runs: pd.DataFrame, rate_col: str = "flow_rate_target_mlh",
                     train_per_rate: int = 3, seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Stratified split: train_per_rate trials from each flow rate go to train, rest to test."""
    rng = np.random.default_rng(seed)
    train_idx, test_idx = [], []
    for _, group in runs.groupby(rate_col):
        idx = group.index.to_list()
        rng.shuffle(idx)
        train_idx.extend(idx[:train_per_rate])
        test_idx.extend(idx[train_per_rate:])
    return runs.loc[train_idx].copy(), runs.loc[test_idx].copy()
