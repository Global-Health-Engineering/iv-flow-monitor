"""Smoke test: the position-overlay render script imports cleanly.

The script renders fig_position_*.png from data/raw/2026-05-13_pm_position_drift/.
We don't execute its main() in CI (the dataset is on disk and the script
would write to analysis/figures/), but we do verify the source loads as
a Python module without raising. This catches syntax / import errors that
would otherwise only surface on the next bench day.
"""

from __future__ import annotations

import importlib.util


def test_build_position_overlay_loads_as_module(repo_root) -> None:
    script_path = repo_root / "tools" / "build_position_overlay.py"
    assert script_path.exists(), "build_position_overlay.py must exist in tools/"
    spec = importlib.util.spec_from_file_location("build_position_overlay", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
