"""C1 — Multi-feature shape regression (requires raw waveform).

Hypothesis: per-drop features (rise time 10-90%, fall time, FWHM, peak,
area, leading/trailing asymmetry coefficient, trailing-edge slope) carry
enough information to fit a position-invariant volume regression.

This module exposes:
  - extract_features(event) -> dict of named features
  - make_algo(weights) -> closure that linearly combines features → V_est

For a 2026-05-14 breadth pass: pull features from all captures, fit a
linear regression of V_true_per_drop against features (cross-validated
leave-one-position-out), report residual K_max/K_min.

Family: shape-feature (C). Status: NEEDS RAW WAVEFORM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass
class C1Features:
    top_rise_10_90_us: float = float("nan")
    top_fall_10_90_us: float = float("nan")
    top_fwhm_us: float = float("nan")
    top_peak_atten: float = float("nan")
    top_area_atten_us: float = float("nan")
    top_asymmetry: float = float("nan")
    bot_rise_10_90_us: float = float("nan")
    bot_fall_10_90_us: float = float("nan")
    bot_fwhm_us: float = float("nan")
    bot_peak_atten: float = float("nan")
    bot_area_atten_us: float = float("nan")
    bot_asymmetry: float = float("nan")
    velocity_mmps: float = float("nan")

    def to_array(self) -> np.ndarray:
        return np.array(list(self.__dict__.values()), dtype=np.float64)

    @classmethod
    def feature_names(cls) -> list[str]:
        return list(cls.__dataclass_fields__.keys())


def _rise_time_10_90(atten: np.ndarray, t_us: np.ndarray, peak: float) -> float:
    """Time from 10% peak crossing to 90% peak crossing on the rising edge."""
    if atten.size < 3 or peak <= 0:
        return float("nan")
    peak_idx = int(np.argmax(atten))
    rising = atten[:peak_idx + 1]
    t_rising = t_us[:peak_idx + 1]
    t10 = _first_crossing(rising, t_rising, 0.1 * peak)
    t90 = _first_crossing(rising, t_rising, 0.9 * peak)
    return float(t90 - t10) if (t10 is not None and t90 is not None) else float("nan")


def _fall_time_10_90(atten: np.ndarray, t_us: np.ndarray, peak: float) -> float:
    if atten.size < 3 or peak <= 0:
        return float("nan")
    peak_idx = int(np.argmax(atten))
    falling = atten[peak_idx:]
    t_falling = t_us[peak_idx:]
    t90 = _first_crossing(falling, t_falling, 0.9 * peak, rising=False)
    t10 = _first_crossing(falling, t_falling, 0.1 * peak, rising=False)
    return float(t10 - t90) if (t10 is not None and t90 is not None) else float("nan")


def _fwhm(atten: np.ndarray, t_us: np.ndarray, peak: float) -> float:
    if atten.size < 3 or peak <= 0:
        return float("nan")
    half = 0.5 * peak
    above = atten >= half
    if not above.any():
        return float("nan")
    idx = np.where(above)[0]
    return float(t_us[idx[-1]] - t_us[idx[0]])


def _first_crossing(arr: np.ndarray, t_us: np.ndarray, level: float,
                    rising: bool = True) -> float | None:
    """Find first index where arr crosses `level` (going up or down)."""
    if rising:
        idx_above = np.where(arr >= level)[0]
        return float(t_us[idx_above[0]]) if idx_above.size else None
    else:
        idx_below = np.where(arr <= level)[0]
        return float(t_us[idx_below[0]]) if idx_below.size else None


def _asymmetry(atten: np.ndarray) -> float:
    if atten.size < 3:
        return float("nan")
    peak_idx = int(np.argmax(atten))
    lead = float(np.sum(atten[:peak_idx + 1]))
    trail = float(np.sum(atten[peak_idx:]))
    return trail / lead if lead > 0 else float("inf")


def extract_features(event, baseline_window_samples: int = 100) -> C1Features:
    if not event.has_raw:
        return C1Features()

    top = event.raw_top.astype(np.float64)
    bot = event.raw_bot.astype(np.float64)
    t_us = event.raw_t_us.astype(np.float64)
    bw = baseline_window_samples

    top_bl = float(np.mean(top[:bw])) if top.size > bw else float(np.mean(top))
    bot_bl = float(np.mean(bot[:bw])) if bot.size > bw else float(np.mean(bot))
    top_atten = np.maximum(top_bl - top, 0.0)
    bot_atten = np.maximum(bot_bl - bot, 0.0)
    top_peak = float(np.max(top_atten))
    bot_peak = float(np.max(bot_atten))

    BEAM_PITCH_MM = 10.0
    G_MMPS2 = 9810.0
    dt_s = event.transit_us * 1e-6 if event.transit_us > 0 else float("nan")
    v_mmps = (BEAM_PITCH_MM / dt_s - 0.5 * G_MMPS2 * dt_s) if dt_s and not np.isnan(dt_s) else float("nan")

    return C1Features(
        top_rise_10_90_us=_rise_time_10_90(top_atten, t_us, top_peak),
        top_fall_10_90_us=_fall_time_10_90(top_atten, t_us, top_peak),
        top_fwhm_us=_fwhm(top_atten, t_us, top_peak),
        top_peak_atten=top_peak,
        top_area_atten_us=float(np.sum(top_atten)),
        top_asymmetry=_asymmetry(top_atten),
        bot_rise_10_90_us=_rise_time_10_90(bot_atten, t_us, bot_peak),
        bot_fall_10_90_us=_fall_time_10_90(bot_atten, t_us, bot_peak),
        bot_fwhm_us=_fwhm(bot_atten, t_us, bot_peak),
        bot_peak_atten=bot_peak,
        bot_area_atten_us=float(np.sum(bot_atten)),
        bot_asymmetry=_asymmetry(bot_atten),
        velocity_mmps=v_mmps,
    )


def make_algo(weights: np.ndarray | None = None, intercept: float = 0.0) -> Callable:
    """If `weights` is None, the algorithm just emits the feature vector
    (volume_uL placeholder = 0). Calling code is expected to:
      1. Run this stub across all captures to collect features
      2. Fit a regression (weights, intercept) against gravimetric truth
      3. Re-instantiate with the fitted weights for the K-fit metric.
    """
    from algo_replay import AlgoResult

    def algo(event):
        feats = extract_features(event)
        if weights is None:
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"features": feats.__dict__, "stage": "extract_only"})
        x = feats.to_array()
        if np.any(np.isnan(x)):
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"reason": "nan_features", "features": feats.__dict__})
        V = float(np.dot(weights, x) + intercept)
        return AlgoResult(volume_uL=V, quality_ok=V > 0,
                          debug={"features": feats.__dict__})

    return algo
