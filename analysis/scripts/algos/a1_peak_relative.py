"""A1 — Peak-relative threshold (requires raw waveform).

Hypothesis: per-drop threshold = baseline + f × (peak - baseline) for some
fixed fraction f. The current firmware uses a baseline + fixed-margin
threshold, which cuts at a different fraction of (peak-baseline) per boot
because baseline drifts 100-200 counts while peak is roughly constant.
A1 normalises this away.

Family: threshold-time (A). Status: NEEDS RAW WAVEFORM — operational once
the 2026-05-14 PM bench has provided DROP_RAW_BEGIN/END blocks via
ENABLE_RAW_CAPTURE=1 firmware.

Parameters to sweep: f in {0.3, 0.5, 0.7}.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np


BEAM_PITCH_MM = 10.0
G_MMPS2 = 9810.0
BEAM_WIDTH_MM = 0.0
V_CAL_K_REFERENCE = 1.27   # baseline K for chord→volume; can refit per algorithm if needed


@dataclass
class A1Params:
    fraction: float = 0.5            # threshold = baseline + f·(peak - baseline)
    baseline_window_samples: int = 100   # leading samples used to estimate baseline


def _crossings(signal: np.ndarray, t_us: np.ndarray, threshold: float) -> tuple[int | None, int | None]:
    """Return (t_in_us, t_out_us) of first rising and last falling threshold crossings."""
    above = signal >= threshold
    if not above.any():
        return None, None
    # First False→True transition
    in_idx = int(np.argmax(above & ~np.r_[False, above[:-1]]))
    # Last True→False transition
    out_idx = int(len(above) - 1 - np.argmax(np.flip(~above & np.r_[above[:-1], False])))
    return int(t_us[in_idx]), int(t_us[out_idx])


def make_algo(params: A1Params | None = None) -> Callable:
    from algo_replay import AlgoResult

    params = params or A1Params()
    f = params.fraction
    bw = params.baseline_window_samples

    def algo(event):
        if not event.has_raw:
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"reason": "no_raw_waveform"})

        top = event.raw_top.astype(np.float64)
        bot = event.raw_bot.astype(np.float64)
        t = event.raw_t_us.astype(np.float64)

        # Baseline = mean of first `bw` samples (pre-trigger period); peak = max.
        top_baseline = float(np.mean(top[:bw])) if top.size > bw else float(np.mean(top))
        bot_baseline = float(np.mean(bot[:bw])) if bot.size > bw else float(np.mean(bot))
        top_peak = float(np.max(top))
        bot_peak = float(np.max(bot))

        top_thresh = top_baseline + f * (top_peak - top_baseline)
        bot_thresh = bot_baseline + f * (bot_peak - bot_baseline)

        tT_in, tT_out = _crossings(top, t, top_thresh)
        tB_in, tB_out = _crossings(bot, t, bot_thresh)
        if None in (tT_in, tT_out, tB_in, tB_out):
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"reason": "incomplete_edges"})

        dt_us = tB_in - tT_in
        tau_us = ((tT_out - tT_in) + (tB_out - tB_in)) // 2
        if dt_us <= 500 or tau_us <= 100:
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"reason": "fast_guard"})

        dt_s = dt_us * 1e-6
        tau_s = tau_us * 1e-6
        v = BEAM_PITCH_MM / dt_s - 0.5 * G_MMPS2 * dt_s
        chord = v * tau_s + 0.5 * G_MMPS2 * tau_s ** 2
        d = chord - BEAM_WIDTH_MM
        V = (math.pi / 6.0) * d ** 3 * V_CAL_K_REFERENCE
        ok = v >= 50.0 and d >= 0.1 and 0 < V <= 500.0
        return AlgoResult(volume_uL=V, quality_ok=ok,
                          debug={"v": v, "d": d, "tau_us": tau_us, "dt_us": dt_us,
                                 "top_thresh": top_thresh, "bot_thresh": bot_thresh,
                                 "top_baseline": top_baseline, "top_peak": top_peak})

    return algo
