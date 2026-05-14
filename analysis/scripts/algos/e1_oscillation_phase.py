"""E1 — Oscillation-phase aware chord correction (requires raw waveform).

Drops in free fall oscillate oblate ↔ prolate at ~10 ms period for the
first 10-30 mm after detaching. The vertical chord time at any single
beam therefore samples the drop at a random phase of this oscillation,
inflating per-drop CV. Two beams 10 mm apart at ~1 m/s catch the drop
~10 ms apart — close to one full oscillation period.

Hypothesis: chord_TOP and chord_BOT, taken together, encode the
oscillation phase. The mean over a full period is the equivalent-sphere
diameter; the phase-detected pair allows that average to be recovered
without averaging across many drops.

Family: oscillation-aware (E). Status: NEEDS RAW WAVEFORM.
Caveat: highly speculative — the oscillation period depends on drop size
and fluid surface tension and isn't a fixed 10 ms. If the breadth pass
shows E1 helps, depth-pass tunes the phase model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np


BEAM_PITCH_MM = 10.0
G_MMPS2 = 9810.0
V_CAL_K_REFERENCE = 1.27


@dataclass
class E1Params:
    baseline_window_samples: int = 100


def make_algo(params: E1Params | None = None) -> Callable:
    from algo_replay import AlgoResult

    params = params or E1Params()
    bw = params.baseline_window_samples

    def algo(event):
        if not event.has_raw:
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"reason": "no_raw_waveform"})

        top = event.raw_top.astype(np.float64)
        bot = event.raw_bot.astype(np.float64)
        t_us = event.raw_t_us.astype(np.float64)

        top_bl = float(np.mean(top[:bw])) if top.size > bw else float(np.mean(top))
        bot_bl = float(np.mean(bot[:bw])) if bot.size > bw else float(np.mean(bot))
        top_atten = np.maximum(top_bl - top, 0.0)
        bot_atten = np.maximum(bot_bl - bot, 0.0)

        # FWHM at each beam ≈ chord time. Use 0.5 × peak as the "diameter
        # crossing" threshold, equivalent to TOP/BOT looking at a half-
        # height drop boundary (more shape-robust than the firmware's
        # absolute threshold).
        top_peak = float(np.max(top_atten))
        bot_peak = float(np.max(bot_atten))
        if min(top_peak, bot_peak) <= 0:
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"reason": "no_pulse"})

        def fwhm_us(atten, t_us, peak):
            above = atten >= 0.5 * peak
            if not above.any():
                return float("nan")
            idx = np.where(above)[0]
            return float(t_us[idx[-1]] - t_us[idx[0]])

        tau_top_us = fwhm_us(top_atten, t_us, top_peak)
        tau_bot_us = fwhm_us(bot_atten, t_us, bot_peak)
        if math.isnan(tau_top_us) or math.isnan(tau_bot_us):
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"reason": "no_fwhm"})

        # Phase-aware average: assume the two chords represent the drop
        # observed at two phases of oscillation. The geometric mean
        # approximates the equivalent-sphere chord better than the
        # arithmetic mean for an oblate↔prolate oscillator.
        tau_avg_s = math.sqrt(tau_top_us * tau_bot_us) * 1e-6

        dt_us = event.transit_us
        if dt_us <= 500:
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"reason": "fast_guard"})
        dt_s = dt_us * 1e-6
        v = BEAM_PITCH_MM / dt_s - 0.5 * G_MMPS2 * dt_s
        chord = v * tau_avg_s + 0.5 * G_MMPS2 * tau_avg_s ** 2
        d = chord    # BEAM_WIDTH_MM = 0
        V = (math.pi / 6.0) * d ** 3 * V_CAL_K_REFERENCE
        ok = v >= 50.0 and d >= 0.1 and 0 < V <= 500.0
        return AlgoResult(volume_uL=V, quality_ok=ok,
                          debug={"tau_top_us": tau_top_us, "tau_bot_us": tau_bot_us,
                                 "tau_avg_us": tau_avg_s * 1e6, "v_mmps": v, "d_mm": d})

    return algo
