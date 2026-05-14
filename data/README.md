# data/

All measurement data — raw UART/scale CSVs, per-drop summaries, geometry
measurements, and gravimetric ground-truth — captured during the
2026-05-13 bench campaign. Everything that feeds the analysis pipeline in
`../analysis/` lives here.

## Layout

```
data/
├── raw/                                    # Bench-captured CSVs (see below)
│   ├── 2026-05-13_macro20_50mlh_*          # Morning V_50_01..05 calibration runs
│   ├── 2026-05-13_pm_position_drift/       # Afternoon mount-height re-test (see docs/limitations.md §17)
│   └── 2026-05-14_pm/                      # Trailing bench session
├── sample/                                  # Representative subset for cold-clone reproducibility
├── geometry.json                            # Beam-separation measurement (single board, n=1)
└── gravimetric_log.csv                      # Scale-derived ground truth, per run
```

## File schemas

### `raw/2026-05-13_macro20_50mlh_*` — main calibration set

One run produces up to four files. Filename pattern:

```
2026-05-13_macro20_50mlh_<NN>_board1.csv          # UART event log (RAW/DROP/CAL rows)
2026-05-13_macro20_50mlh_<NN>_board1.log          # Raw UART text capture (audit trail)
2026-05-13_macro20_50mlh_<NN>_board1_perdrop.csv  # Per-drop summary (transit + pulses + volume)
2026-05-13_macro20_50mlh_<NN>_board1_scale.csv    # Gravimetric scale stream (timestamped grams)
```

`<NN>` is the run index (`01`..`05`, plus `_test`, `_03_streaming`, and `_04_aborted` variants).

UART CSV columns:

```
abs_ms, drop_N, transit_us, pulse_top_us, pulse_bot_us,
v_cmps, d_0.1mm, V_0.1uL, state, Q_cmLph, top_raw, bot_raw
```

`_perdrop.csv` is the post-processed condensation produced by
`../analysis/scripts/load_run.py` — one row per detected drop, aligned
to the scale stream:

```
uart_idx, step_idx, t_uart_rel_ms, t_step_rel_ms, t_lag_ms,
delta_g, v_true_uL, v_est_uL, v_diff_uL
```

`_scale.csv` is the scale stream sampled at ~23 Hz:

```
t_ms, mass_g, status
```

### `raw/2026-05-13_pm_position_drift/`

Afternoon mount-height re-test that produced the §17 position-dependence
finding (`docs/limitations.md` §17). Per-run README inside the folder
documents each mount position and the K-value required to make the
LCD-summed drop volume match the gravimetric reading at that position.

### `raw/2026-05-14_pm/`

Trailing bench captures from the day after the main campaign — kept for
provenance; not used in the headline V_50 results.

### `geometry.json`

Single-board beam-separation measurement with caliper repeats. Schema:

```json
{
  "beam_separation_mm":         {"mean": 10.2, "sd": 0.3, "n_boards_measured": 1, "cad_nominal_mm": 10.0},
  "caliper_resolution_mm":      0.05,
  "positioning_uncertainty_mm": 0.5,
  "measured_by":                "digital calipers",
  "measurement_date":           "2026-05-07"
}
```

`n_boards_measured = 1` — board-to-board scatter is un-quantified for
Rev-B and named explicitly in `docs/limitations.md` §8.

### `gravimetric_log.csv`

Per-run summary table. One row per run with:

```
run_id, csv_filename, flow_rate_target_mlh, gravimetric_mass_g,
run_duration_s, drop_count_device, notes
```

`V_true_chamber = gravimetric_mass_g / drop_count_device` (computed in
the analysis notebook) is the per-run chamber-drop ground truth used by
`../analysis/notebooks/validation.ipynb`. The `notes` column records the
firmware-constants context for each run.

## Reproducibility

`sample/` exists so the analysis notebook in `../analysis/` runs
end-to-end even without access to the full dataset. The Docker pipeline
`docker compose up regenerate-figures-sample` uses `sample/` only and is
the path exercised by CI.

The complete dataset will be deposited on Zenodo under CC BY 4.0; DOI
will be added here on mint.

## FAIR principles

- **Findable** — files referenced from this README and the Pages site;
  Zenodo DOI on submission.
- **Accessible** — public GitHub repository, no authentication.
- **Interoperable** — plain CSV with documented column meanings and units;
  JSON for structured metadata.
- **Reusable** — CC BY 4.0; provenance captured in the per-run UART log
  files; per-run gravimetric reference preserved alongside the UART
  streams.
