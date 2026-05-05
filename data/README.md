# data/

All measurement data — raw CSVs, calibration logs, geometry measurements,
session metadata, and edge-case observations. Everything that feeds the
analysis pipeline in `../analysis/`.

The naming conventions and on-disk schemas in this folder are
**pre-registered** in `../docs/testing-and-validation.md` and must not be
changed mid-campaign without a noted protocol amendment.

## Layout

```
data/
├── raw/                            # Official EXP-3 + EXP-4 validation runs
│   └── YYYY-MM-DD_macro20_XXmlh_trialN_boardX.csv
├── shakeout/                       # EXP-2 firmware debugging runs (not pre-registered)
│   └── YYYY-MM-DD_shakeout_NN.csv
├── edge_cases/                     # EXP-5 edge-case observations
│   └── EC_XX_YYYY-MM-DD.md
├── sample/                         # Sample subset for cold-clone reproducibility test
│   └── (3–4 representative CSVs from raw/)
├── calibration_log.csv             # EXP-0 threshold calibration results, append-only
├── geometry.json                   # EXP-1 beam-separation measurements per board
└── session_log.csv                 # Per-session metadata: board, head height, env conditions
```

## File schemas

### `raw/*.csv` — official validation runs (EXP-3, EXP-4)

One row per drop event, one file per 5-minute run.

```
abs_ms,drop_N,transit_us,pulse_top_us,pulse_bot_us,top_raw,bot_raw
```

Filename pattern (case-sensitive):

- EXP-3 (Rev-B): `YYYY-MM-DD_macro20_<rate>mlh_trial<N>_board<X>.csv`
- EXP-4 (Rev-A baseline): `YYYY-MM-DD_revA_macro20_<rate>mlh_trial<N>_board<X>.csv`

Examples: `2026-05-07_macro20_50mlh_trial1_board1.csv`,
`2026-05-08_revA_macro20_20mlh_trial1_board2.csv`.

### `calibration_log.csv` — EXP-0, append-only

```
date,board_id,mode,thresh_top,thresh_bot,baseline_top_mean,baseline_bot_mean,false_pos_60s,notes
```

`mode` is one of `manual` or `auto`. `false_pos_60s` is the count from the
EXP-0 step-7 verification gate; the gate fails if non-zero.

### `geometry.json` — EXP-1, one entry per board

```json
{
  "beam_separation_mm":        {"mean": 14.2, "sd": 0.3, "n_boards_measured": 5, "cad_nominal_mm": 14.0},
  "caliper_resolution_mm":     0.05,
  "positioning_uncertainty_mm": 0.5,
  "measured_by":               "digital calipers",
  "measurement_date":          "2026-05-07",
  "notes": "positioning uncertainty estimated from repeated placement; dominates over caliper resolution"
}
```

### `session_log.csv` — per-session metadata

```
date,board_id,head_height_cm,room_temp_c,light_condition,notes
```

Add a row at the **start** of each bench session. `notes` may include
discard reasons (per the pre-registered discard rule in
`../docs/testing-and-validation.md` EXP-3) and the firmware commit hash
when running Rev-A baseline (EXP-4).

### `edge_cases/EC_XX_YYYY-MM-DD.md` — EXP-5, one file per scenario

Each file uses the **pre-defined** five-column format:

```
| Scenario | False events in 60 s | Observed LCD behaviour | Root cause hypothesis | Proposed Rev-C mitigation |
```

Defining the schema before the data rules out post-hoc shaping of the
Discussion section.

## Discard rule (pre-registered, EXP-3)

Runs are discarded and re-collected if any of the following occur:

- Tubing kinked or flow visibly disrupted mid-run
- Scale reading shows clearly incorrect mass (container shifted)
- CSV shows >5 s gap in drop events without roller adjustment
  (firmware crash or alignment loss)
- Flow stabilisation criterion not met before timer started **and** this
  was not logged

Discarded runs stay in `raw/` with the discard reason logged in
`session_log.csv`. Do not delete data.

## Reproducibility

`sample/` exists so the analysis notebook in `../analysis/` runs end-to-end
even without access to the full dataset. The cold-clone test
(`../docs/external-reproducibility.md`, planned for 2026-05-13) will use
`sample/` only.

The complete dataset is also deposited on Zenodo with DOI
*(populated at submission)* under CC-BY 4.0.
