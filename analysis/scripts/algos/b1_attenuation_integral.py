"""B1 — Integral of attenuation × velocity (requires raw waveform).

By geometric identity, for a thin beam:

    Volume ∝ ∫ (baseline - signal) dt × v

where v is the drop velocity at the beam. The integral measures total
light occluded over time → directly proportional to drop projection area
× transit time, which equals drop volume for a sphere of any shape under
mild assumptions. Position-invariant by construction if the baseline is
correct.

Family: integral (B). Status: NEEDS RAW WAVEFORM.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np


BEAM_PITCH_MM = 10.0
G_MMPS2 = 9810.0


@dataclass
class B1Params:
    baseline_window_samples: int = 100
    use_top_only: bool = False    # if True, ignore BOT (umbilical-cleanest channel)
    use_bot_only: bool = False


def make_algo(params: B1Params | None = None) -> Callable:
    from algo_replay import AlgoResult

    params = params or B1Params()
    bw = params.baseline_window_samples

    def algo(event):
        if not event.has_raw:
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"reason": "no_raw_waveform"})

        top = event.raw_top.astype(np.float64)
        bot = event.raw_bot.astype(np.float64)
        t_us = event.raw_t_us.astype(np.float64)

        top_baseline = float(np.mean(top[:bw])) if top.size > bw else float(np.mean(top))
        bot_baseline = float(np.mean(bot[:bw])) if bot.size > bw else float(np.mean(bot))

        # Attenuation = baseline - signal (positive when drop occludes beam).
        top_atten = np.maximum(top_baseline - top, 0.0)
        bot_atten = np.maximum(bot_baseline - bot, 0.0)

        # Per-sample dt (µs) — robust against non-uniform polled sampling.
        if t_us.size < 2:
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"reason": "no_time_axis"})
        dt_us = np.diff(t_us)
        dt_us = np.append(dt_us, dt_us[-1])   # extend to match length

        if params.use_top_only:
            atten_integral = float(np.sum(top_atten * dt_us))    # ADC counts × µs
        elif params.use_bot_only:
            atten_integral = float(np.sum(bot_atten * dt_us))
        else:
            atten_integral = float(np.sum((top_atten + bot_atten) * 0.5 * dt_us))

        # Estimate drop velocity from edge-time data passed alongside the
        # event (transit_us). This couples B1 to the existing Schmitt edges
        # for v but not for shape — clean separation.
        transit_us = event.transit_us
        if transit_us <= 500:
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"reason": "fast_guard"})
        dt_s = transit_us * 1e-6
        v_mmps = BEAM_PITCH_MM / dt_s - 0.5 * G_MMPS2 * dt_s
        if v_mmps < 50.0:
            return AlgoResult(volume_uL=0.0, quality_ok=False,
                              debug={"reason": "v_low"})

        # V (uL) ∝ atten_integral (counts·µs) × v (mm/s) × geometric_K
        # The proportionality constant is determined empirically by fitting
        # against gravimetric truth; the K we report here is the algorithm-
        # specific scale factor.
        # For breadth pass: report the integral × v as the "raw" V_est,
        # let evaluate() compute the K-fit per position.
        V_raw = atten_integral * v_mmps * 1e-9   # arbitrary unit, K absorbs

        return AlgoResult(volume_uL=V_raw, quality_ok=True,
                          debug={"atten_integral": atten_integral, "v_mmps": v_mmps,
                                 "top_baseline": top_baseline, "bot_baseline": bot_baseline})

    return algo
