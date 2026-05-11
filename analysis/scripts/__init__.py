"""Analysis helpers for the Dripito validation pipeline.

Each module has one purpose. Import the public function you need:

    from scripts.load_run import load_run
    from scripts.calibration_fit import fit_correction_factor
    from scripts.bland_altman import bland_altman_plot
    from scripts.bootstrap_mape import bootstrap_mape

The notebooks/validation.ipynb wires them together; pytest in
tests/ targets them independently.
"""
