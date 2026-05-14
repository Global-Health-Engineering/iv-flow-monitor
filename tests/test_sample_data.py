"""Smoke tests that the cold-clone reproducibility sample data is intact.

The repo promises (README + analysis/README) that a fresh clone can
regenerate every figure from `data/sample/`. These tests verify the
files exist, are non-empty, and have the expected schema.
"""

from __future__ import annotations

import json

import pandas as pd


def test_sample_csvs_exist_and_have_drop_data(sample_data_dir) -> None:
    for name in (
        "sample_macro20_20mlh.csv",
        "sample_macro20_50mlh.csv",
        "sample_macro20_100mlh.csv",
    ):
        csv_path = sample_data_dir / name
        assert csv_path.exists(), f"missing sample CSV: {name}"
        df = pd.read_csv(csv_path)
        assert len(df) > 0, f"sample CSV {name} is empty"
        for col in ("abs_ms", "drop_N", "transit_us", "pulse_top_us", "pulse_bot_us"):
            assert col in df.columns, f"sample CSV {name} missing column {col}"


def test_geometry_json_loads(geometry_json) -> None:
    assert geometry_json.exists(), "data/sample/geometry.json must exist"
    with geometry_json.open() as f:
        geometry = json.load(f)
    assert isinstance(geometry, dict), "geometry.json should be a JSON object"
