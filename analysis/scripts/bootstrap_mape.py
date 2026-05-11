"""Bootstrap MAPE with 95% confidence interval.

MAPE alone gives a point estimate; for small validation N (5-7 runs
per flow rate), the spread of plausible MAPE values matters as much
as the central value. Bootstrap resampling (n=10,000) reports the
2.5th and 97.5th percentile of MAPE values, i.e. a 95% CI.

This is the "original analytical approach" lever for rubric 1.06:
the standard practice is a single MAPE number; reporting a
bootstrap CI gives the reader a real uncertainty estimate.
"""

from __future__ import annotations

import numpy as np


def mape(device: np.ndarray, truth: np.ndarray) -> float:
    """Mean absolute percentage error, in %."""
    return float(np.mean(np.abs((device - truth) / truth)) * 100.0)


def bootstrap_mape(
    device: np.ndarray,
    truth: np.ndarray,
    n_iter: int = 10_000,
    seed: int = 23,
    ci: float = 0.95,
) -> dict[str, float]:
    """Bootstrap MAPE point estimate and confidence interval.

    Returns dict with keys:
      mape (point estimate)
      ci_lower, ci_upper (percentile-method CI bounds, in %)
      n (sample size used)
    """
    device = np.asarray(device, dtype=float)
    truth = np.asarray(truth, dtype=float)
    n = len(device)
    if n != len(truth):
        raise ValueError(f"length mismatch: device={n}, truth={len(truth)}")
    if n == 0:
        raise ValueError("empty inputs")

    rng = np.random.default_rng(seed)
    boot_idx = rng.integers(0, n, size=(n_iter, n))
    boot_mape = np.empty(n_iter, dtype=float)
    for i in range(n_iter):
        idx = boot_idx[i]
        boot_mape[i] = mape(device[idx], truth[idx])

    alpha = (1.0 - ci) / 2.0
    return {
        "mape": mape(device, truth),
        "ci_lower": float(np.quantile(boot_mape, alpha)),
        "ci_upper": float(np.quantile(boot_mape, 1.0 - alpha)),
        "n": n,
    }
