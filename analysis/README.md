# analysis/

Reproducible data analysis pipeline. Takes raw CSVs from `../data/` and
produces every figure, table, and number quoted in `../docs/results.md`.

## Layout

```
analysis/
├── notebooks/
│   ├── calibration.ipynb        # EXP-0 sweep + threshold log visualisation
│   ├── geometry.ipynb           # EXP-1 beam-separation summary
│   ├── validation.ipynb         # EXP-3/4/6 main analysis: Bland-Altman + MAPE
│   └── edge_cases.ipynb         # EXP-5 summary table generation
├── figures/                     # Generated PNGs (committed for README embedding)
│   ├── fig_calibration_sweep.png
│   ├── fig_bland_altman_combined.png
│   ├── fig_bland_altman_per_rate.png
│   ├── fig_mape_table.png
│   ├── fig_error_vs_flow.png
│   └── fig_drop_volume_distribution.png
├── scripts/                     # Reusable Python helpers (one purpose each)
│   ├── load_run.py              # Parse a raw/*.csv into a DataFrame
│   ├── calibration_fit.py       # Fit scalar correction k by least-squares
│   ├── bland_altman.py          # Bland-Altman with 95% LoA
│   └── bootstrap_mape.py        # Bootstrap MAPE 95% CI (n=10000)
├── requirements.txt             # Pinned via pip-compile (see below)
├── requirements.in              # Top-level deps; pip-compile produces requirements.txt
└── Dockerfile                   # docker compose up → regenerate every figure
```

## Reproducing the analysis

### Quick (host Python)

```bash
cd analysis/
python -m venv .venv && source .venv/bin/activate     # POSIX
# .venv\Scripts\Activate.ps1                          # Windows PowerShell
pip install -r requirements.txt
jupyter lab notebooks/validation.ipynb
```

### Reference (Docker, the version that gates the cold-clone test)

```bash
docker compose up regenerate-figures
```

This rebuilds every PNG in `figures/` from scratch using the dataset under
`../data/`. Pinned Python + Jupyter + scientific-stack versions live in
the Dockerfile. Use this for the 2026-05-13 cold-clone reproducibility
test (`../docs/external-reproducibility.md`).

### With sample data only (no full dataset on disk)

```bash
docker compose up regenerate-figures-sample
```

Runs the same pipeline against `../data/sample/` instead of
`../data/raw/`. Produces shaped-but-not-meaningful plots — useful to
prove the pipeline runs, not to draw conclusions.

## Pinning policy

- `requirements.in` is hand-edited and lists top-level dependencies
  (numpy, pandas, scipy, matplotlib, jupyter, scikit-learn).
- `requirements.txt` is **generated** from `requirements.in` by
  `pip-compile --generate-hashes`. Do not hand-edit. Re-run `pip-compile`
  whenever `requirements.in` changes.
- Dockerfile pins the base Python image with a fixed digest (not just
  `python:3.11`).
- Jupyter notebooks store their last execution output, but the
  CI / cold-clone test runs them headless via `papermill` to verify they
  re-execute cleanly from `Run All`.

## What lives in figures/

PNGs are committed (not just generated) so the top-level README and
`../docs/results.md` can embed them without requiring a build step. They
are regenerable — the source of truth is the notebook + raw data, not the
PNG. CI verifies that re-running the notebook produces a
byte-identical-or-numerically-equivalent figure.

## CI integration

GitHub Actions [`.github/workflows/build-and-test.yml`](../.github/workflows/build-and-test.yml) runs on every push to `v2`:

1. **`pytest`** against `tests/` (analysis helpers + tools smoke tests).
2. **`verify_estimator.py`** — Monte-Carlo verification of the firmware drop-size math.
3. **Docker-built analysis pipeline** — regenerates `figures/fig_error_budget.png` and the validation figures from `data/sample/`, then uploads them as a workflow artifact.

A green badge on the top-level README is the user-visible artefact.

## Why a reproducible pipeline (and not a polished PDF report)

A reader can rerun this analysis on different data, with a tweaked
correction factor, or with the macro-20 limitation lifted in a future
revision. A PDF cannot. The repo's value as an artefact compounds with
that re-runnability.
