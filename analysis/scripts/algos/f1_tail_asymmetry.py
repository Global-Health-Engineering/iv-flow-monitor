"""F1 — Tail-energy asymmetry contamination filter (requires raw waveform).

Hypothesis: clean drops produce roughly symmetric pulses (rise mirrors
fall). Umbilical/splash contamination extends the TRAILING edge only,
creating asymmetry. Compute the ratio of trailing-edge energy to
leading-edge energy; reject drops with ratio > threshold.

Family: contamination-rejection (F). Status: NEEDS RAW WAVEFORM.
Once we have raw data, also useful as a per-drop "contamination score"
visualisation regardless of whether the rejection improves K-fit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass
class F1Params:
    asymmetry_reject_ratio: float = 2.0    # tail/lead energy > this → reject
    baseline_window_samples: int = 100


def _split_at_peak(signal: np.ndarray, baseline: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (leading_half, trailing_half) attenuation arrays around peak."""
    atten = np.maximum(baseline - signal, 0.0)
    if atten.size == 0:
        return atten, atten
    peak_idx = int(np.argmax(atten))
    return atten[:peak_idx + 1], atten[peak_idx:]


def asymmetry_score(event, channel: str = "top", bw: int = 100) -> float:
    """Compute the tail/lead energy ratio for one beam. >1 → trailing heavy."""
    if not event.has_raw:
        return float("nan")
    sig = (event.raw_top if channel == "top" else event.raw_bot).astype(np.float64)
    baseline = float(np.mean(sig[:bw])) if sig.size > bw else float(np.mean(sig))
    lead, trail = _split_at_peak(sig, baseline)
    lead_energy = float(np.sum(lead))
    trail_energy = float(np.sum(trail))
    if lead_energy <= 0:
        return float("inf")
    return trail_energy / lead_energy


def make_algo(params: F1Params | None = None) -> Callable:
    """F1 doesn't compute its own volume — it returns the reference
    chord-time volume but flags quality_ok=False for drops above the
    asymmetry threshold on EITHER beam."""
    from algo_replay import AlgoResult, algo_reference

    params = params or F1Params()
    bw = params.baseline_window_samples
    threshold = params.asymmetry_reject_ratio

    def algo(event):
        ref = algo_reference(event)
        top_score = asymmetry_score(event, "top", bw)
        bot_score = asymmetry_score(event, "bot", bw)
        contaminated = (top_score > threshold) or (bot_score > threshold)
        return AlgoResult(
            volume_uL=ref.volume_uL,
            quality_ok=ref.quality_ok and not contaminated,
            debug={"top_asymmetry": top_score, "bot_asymmetry": bot_score,
                   "contaminated": contaminated, **ref.debug},
        )

    return algo
