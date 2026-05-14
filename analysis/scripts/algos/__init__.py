"""Algorithm library for the 2026-05-14 PM offline exploration phase.

Each algorithm is a Python module exposing a `volume_estimate(event, **params)`
function with the AlgoResult contract from `algo_replay.py`. They're organised
by family:

  threshold-time   : a1_peak_relative
  integral         : b1_attenuation_integral
  shape-feature    : c1_shape_features
  contamination-rj : f1_tail_asymmetry, f4_pulse_outlier
  oscillation-aware: e1_oscillation_phase

A1, B1, C1, E1, F1 require the raw beam waveform (DropEvent.raw_top/raw_bot);
F4 operates on edge-time data alone and is the only family-member that can be
exercised against yesterday's 2026-05-13 dataset before today's bench session.
"""
