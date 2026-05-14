"""Shared pytest fixtures and path setup for the repo's test suite.

Tests import from `analysis/scripts/`, `tools/`, and the firmware tools
folder; this file makes them all reachable as top-level modules and
exposes a few canonical filesystem paths.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Make the analysis scripts importable without installing the repo.
sys.path.insert(0, str(REPO_ROOT / "analysis" / "scripts"))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def sample_data_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "sample"


@pytest.fixture(scope="session")
def sample_csv(sample_data_dir: Path) -> Path:
    return sample_data_dir / "sample_macro20_50mlh.csv"


@pytest.fixture(scope="session")
def geometry_json(sample_data_dir: Path) -> Path:
    return sample_data_dir / "geometry.json"
