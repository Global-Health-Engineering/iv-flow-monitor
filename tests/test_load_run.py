"""Smoke tests for analysis/scripts/load_run.py against data/sample/.

These verify that the per-drop physics chain implemented in load_run.py
(gravity-corrected velocity, mean-of-pulses chord, sphere volume, V_CAL_K
scalar) parses real bench data without exploding and produces
sane-magnitude derived columns. Tight numerical assertions are deferred
to the validation notebook; tests here gate the pipeline against
regressions in the loader.
"""

from __future__ import annotations

from load_run import BEAM_WIDTH_MM, G_MPS2, V_CAL_K, load_run, summarise_run


def test_v_cal_k_matches_firmware() -> None:
    """V_CAL_K constant mirrors the firmware #define in main.c."""
    assert V_CAL_K == 1.27


def test_g_mps2_is_standard_gravity() -> None:
    """Gravity constant matches the firmware G_MMPS2 / 1000 convention."""
    assert G_MPS2 == 9.81


def test_beam_width_is_point_approximation() -> None:
    """BEAM_WIDTH_MM = 0 mirrors the firmware Rev-B point-beam convention."""
    assert BEAM_WIDTH_MM == 0.0


def test_load_run_parses_sample_csv(sample_csv) -> None:
    """load_run can parse a sample CSV and return a non-empty DataFrame."""
    df = load_run(sample_csv, beam_separation_mm=10.2)
    assert len(df) > 0, "expected drop events in the sample CSV"


def test_load_run_adds_derived_columns(sample_csv) -> None:
    """The loader adds the physics-chain columns the analysis depends on."""
    df = load_run(sample_csv, beam_separation_mm=10.2)
    for col in ("velocity_m_s", "drop_diameter_mm", "drop_volume_uL"):
        assert col in df.columns, f"missing derived column: {col}"


def test_load_run_velocities_are_physical(sample_csv) -> None:
    """v at TOP for falling drops should be positive and below 5 m/s."""
    df = load_run(sample_csv, beam_separation_mm=10.2)
    assert (df["velocity_m_s"] > 0).all(), "drops should be falling (v > 0)"
    assert (df["velocity_m_s"] < 5).all(), "drops should not exceed 5 m/s"


def test_load_run_drop_volumes_are_physical(sample_csv) -> None:
    """Drop volumes should fall in a physically plausible IV-drip range."""
    df = load_run(sample_csv, beam_separation_mm=10.2)
    assert (df["drop_volume_uL"] > 1).all(), "drops below 1 µL are non-physical for IV"
    assert (df["drop_volume_uL"] < 1000).all(), "drops above 1 mL are non-physical for IV"


def test_load_run_drop_count_field_is_monotonic(sample_csv) -> None:
    """drop_N from the firmware should be non-decreasing per row."""
    df = load_run(sample_csv, beam_separation_mm=10.2)
    diffs = df["drop_N"].diff().dropna()
    assert (diffs >= 0).all(), "drop_N should be monotonically non-decreasing"


def test_load_run_rejects_csv_missing_columns(tmp_path) -> None:
    """The loader raises if a required column is missing."""
    import pandas as pd
    bad_csv = tmp_path / "bad.csv"
    pd.DataFrame({"abs_ms": [0], "drop_N": [1]}).to_csv(bad_csv, index=False)
    try:
        load_run(bad_csv, beam_separation_mm=10.2)
    except ValueError as e:
        assert "missing columns" in str(e)
    else:
        raise AssertionError("expected ValueError for CSV missing required columns")


def test_summarise_run_returns_expected_keys(sample_csv) -> None:
    """summarise_run returns the run-level dict the analysis depends on."""
    df = load_run(sample_csv, beam_separation_mm=10.2)
    summary = summarise_run(df, duration_s=60.0)
    for key in (
        "drop_count",
        "total_volume_uL",
        "device_flow_mlh",
        "mean_drop_volume_uL",
        "mean_velocity_m_s",
        "transit_us_cv",
    ):
        assert key in summary, f"summary missing key: {key}"
