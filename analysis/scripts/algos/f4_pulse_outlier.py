"""F4 — Pulse-duration outlier rejection (edge-time only, no raw waveform).

Hypothesis: at a given drop velocity v, clean drops produce a narrow τ
(pulse-mean) distribution. Outliers (umbilical-extended TOP_low,
splash-extended BOT_low) sit in the tail of that distribution and can be
filtered without touching the volume math itself.

Approach:
  1. Compute v_mmps and τ_us = mean(pulse_top, pulse_bot) per drop using the
     canonical firmware math.
  2. For each population (one position at a time), fit a 1st-degree polynomial
     τ(v) on the inliers (initial pass = all drops).
  3. Compute residual = τ - τ̂(v). Reject drops with |residual| > REJECT_K · σ
     where σ is the population's residual standard deviation.
  4. Volume estimate is the canonical chord formula; the algorithm's value-add
     is the rejection flag, not a different K.

This is implementable in firmware as a running median + MAD on (v, τ) — Rev-C
candidate if it shows position-invariance gains in offline replay.

Family: contamination-rejection (F).
Status: edge-time data only — testable against the 2026-05-13 dataset.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass
class F4Params:
    reject_k_sigma: float = 3.0
    min_inliers_for_fit: int = 5


# Firmware constants — must match algo_replay.py
BEAM_PITCH_MM = 10.0
G_MMPS2 = 9810.0
BEAM_WIDTH_MM = 0.0


def _firmware_chord_volume(transit_us: int, pulse_mean_us: int) -> tuple[float, float, float, float]:
    """Return (v_mmps, d_mm, vol_uL_no_K, quality_ok_basic)."""
    dt_s = transit_us * 1e-6
    tau_s = pulse_mean_us * 1e-6
    v_mmps = BEAM_PITCH_MM / dt_s - 0.5 * G_MMPS2 * dt_s
    chord_mm = v_mmps * tau_s + 0.5 * G_MMPS2 * tau_s ** 2
    d_mm = chord_mm - BEAM_WIDTH_MM
    vol_uL_no_K = (math.pi / 6.0) * d_mm ** 3
    ok = (transit_us > 500 and pulse_mean_us > 100 and v_mmps >= 50.0
          and d_mm >= 0.1 and vol_uL_no_K > 0.0 and vol_uL_no_K <= 500.0 / 1.27)
    return v_mmps, d_mm, vol_uL_no_K, ok


def fit_rejection_mask(events, params: F4Params | None = None) -> np.ndarray:
    """Compute an (n_events,) bool array: True = keep, False = reject.

    Operates on a HOMOGENEOUS population (one mount position). Caller is
    responsible for partitioning multi-position data.
    """
    params = params or F4Params()
    n = len(events)
    if n == 0:
        return np.array([], dtype=bool)

    v_arr = np.empty(n, dtype=np.float64)
    tau_arr = np.empty(n, dtype=np.float64)
    basic_ok = np.empty(n, dtype=bool)
    for i, ev in enumerate(events):
        pulse_mean = (ev.pulse_top_us + ev.pulse_bot_us) // 2
        v, _d, _V, ok = _firmware_chord_volume(ev.transit_us, pulse_mean)
        v_arr[i] = v
        tau_arr[i] = pulse_mean
        basic_ok[i] = ok

    mask = basic_ok.copy()
    if mask.sum() < params.min_inliers_for_fit:
        return mask

    # Linear fit τ = a·v + b on current inliers; iterate once (single re-fit).
    for _ in range(2):
        inliers = np.where(mask)[0]
        if inliers.size < params.min_inliers_for_fit:
            break
        coeffs = np.polyfit(v_arr[inliers], tau_arr[inliers], 1)
        predicted = np.polyval(coeffs, v_arr)
        resid = tau_arr - predicted
        sigma = np.std(resid[inliers])
        if sigma <= 0:
            break
        new_mask = basic_ok & (np.abs(resid) <= params.reject_k_sigma * sigma)
        if np.array_equal(new_mask, mask):
            break
        mask = new_mask

    return mask


def make_algo(rejection_mask: np.ndarray | None = None) -> Callable:
    """Return an algo(event) -> AlgoResult closure.

    Two usage patterns:
      1. Call fit_rejection_mask(events) → mask, then make_algo(mask) for
         use with `evaluate()`. The closure indexes into the mask by
         event_index (caller iterates in the same order).
      2. Call make_algo(None) for the unfiltered baseline (no rejection).
    """
    from algo_replay import AlgoResult  # local import to avoid circular at module load

    # Index counter persists across calls — caller must process events in the
    # same order they were used to build the mask.
    state = {"i": 0}

    V_CAL_K = 1.27   # canonical K; F4 doesn't refit K

    def algo(event):
        idx = state["i"]
        state["i"] += 1
        pulse_mean = (event.pulse_top_us + event.pulse_bot_us) // 2
        v, d, V_no_K, ok = _firmware_chord_volume(event.transit_us, pulse_mean)
        V = V_no_K * V_CAL_K
        quality_ok = ok
        if rejection_mask is not None and idx < rejection_mask.size:
            quality_ok = quality_ok and bool(rejection_mask[idx])
        return AlgoResult(
            volume_uL=V if quality_ok else 0.0,
            quality_ok=quality_ok,
            debug={"v_mmps": v, "d_mm": d, "tau_us": pulse_mean, "f4_kept": quality_ok},
        )

    return algo
