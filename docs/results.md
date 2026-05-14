# Results

Validation of the Rev-B dual-beam drop-volume monitor against gravimetric ground truth, 2026-05-13. Four 10-minute calibration runs (V_50_01..04) plus one streaming-regime sample (`V_streaming`) characterise the device's behaviour across a 39–186 µL chamber-drop range.

Headline finding: **after applying a single scalar correction `V_CAL_K = 1.27`, the device's per-run mean volume tracks gravimetric ground truth to within ±30 % across the four calibration runs (V_50_01..04)**. A ±30 % per-run spread is far outside any clinical accuracy target; Rev-B is a working dual-beam architecture demonstrator, not a clinically deployable monitor. Residual error sources are inventoried in [`limitations.md`](limitations.md).

## Bench dataset

| Field | Value |
|---|---|
| Date | 2026-05-13 |
| Drip set | nominal macro 20 gtt/mL (see `docs/limitations.md`) |
| Fluid | Water, ρ = 1.000 g/mL |
| Beam separation | 10.2 mm (`data/geometry.json`) |
| Runs | V_50_01, V_50_02, V_50_03, V_50_04 (with caveat); plus V_streaming sample (continuous-flow regime, documented separately in `docs/bench/2026-05-13_V_streaming.md`) |
| Firmware constants | `BEAM_WIDTH_MM=0.0`, `CAL_MARGIN_HIGH=100`, `CAL_MARGIN_LOW=30`, `D_MM_MIN=0.1`, `V_CAL_K=1.27` |

Each run records two side-channel streams in parallel:
- Firmware DROP rows over UART (12-column CSV; `data/raw/*.csv`)
- Mettler-Toledo MS scale via SICS `SIR` at ~23 Hz (`data/raw/*_scale.csv`)

## Ground-truth definition

Per-drop ground truth is the per-run **chamber-orifice** gravimetric average:

```
V_true_chamber = total_mass_g × 1000 / N_UART_chamber_drops   (µL per chamber drop)
```

This is the only valid pairing between the device measurement and the scale at the per-drop level. The scale captures mass at the **end-of-tubing orifice**, which has different geometry than the chamber orifice and drips at a different rate (see `docs/limitations.md` §Two-orifice divergence). Mass conservation gives:

```
N_chamber × V_chamber = N_end × V_end = total mass
```

so total mass is a clean shared quantity, but `N_chamber ≠ N_end`. The 2026-05-13 campaign typically saw end-orifice drop counts 1.5–2× the chamber-drop counts. Per-drop matching of UART events to scale steps is preserved only as an exploratory diagnostic (`tools/match_scale_drops.py`).

In clinical use the two-orifice gap collapses: with a catheter in a vein, the fluid column is closed at the patient end and the chamber-drop count equals the volume actually delivered. The divergence is a bench-measurement artefact of dripping into open air, not a clinical-accuracy concern.

## Per-run summary

All `V_est` figures below come from `load_run.py`, which mirrors the firmware physics exactly: gravity-corrected `v_TOP = L/dt − ½g·dt`, mean-of-pulses chord time, sphere-volume conversion, then the `V_CAL_K = 1.27` scalar. The uncalibrated chord-sphere number is `V_est_calibrated / 1.27`.

| Run | Duration (s) | N drops | Mass (g) | Grav flow (mL/h) | V_true_chamber (µL) | V_est_calibrated (µL) | k_post = V_true / V_est | Direction |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| V_50_01 | 185.6 | 65 | 4.7992 | 93.09 | 73.83 | 58.35 | 1.27 | device under |
| V_50_02 | 573.5 | 339 | 13.3097 | 83.55 | 39.26 | 49.84 | 0.79 | device over |
| V_50_03 | 600.0 | 180 | 10.6780 | 64.07 | 59.32 | 57.29 | 1.04 | within noise |
| V_50_04 | 600.0 | 40 (gap) | 7.4441 | 44.66 | ≤186.10 | 208.44 | ≥0.89 | exploratory |
| V_streaming | 141 | 66 | — | ≈ 269 | — | range 0.3–183 µL (regime breakdown) | — | streaming regime |

mean(k_post) across V_50_01..04 = 0.995 (well within rounding of 1.0, as expected since `V_CAL_K` is the mean of these four runs' `k_pre`). Worst-case per-run deviation is V_50_01 (1.27×, device under-reads by 21%) and V_50_02 (0.79×, device over-reads by 27%). The k_post spread of 0.79–1.27 is the ±30 % residual referenced in the headline.

Detail per run: `docs/bench/2026-05-13_V_50_0{1,2,3,4}.md` and `docs/bench/2026-05-13_V_streaming.md`.

## How `V_CAL_K` was chosen

`V_CAL_K = 1.27` is the unweighted mean of the per-run `k_pre = V_true_chamber / V_est_uncalibrated` values across V_50_01..04 (gravity-corrected mean-pulse model):

| Run | V_true_chamber (µL) | V_est_uncalibrated (µL) | k_pre |
|---|---:|---:|---:|
| V_50_01 | 73.83 | 45.95 | 1.607 |
| V_50_02 | 39.26 | 39.24 | 1.001 |
| V_50_03 | 59.32 | 45.11 | 1.315 |
| V_50_04 | 186.10 | 164.13 | 1.134 |
| **Mean** |   |   | **1.264** |

Rounded to two decimals → `V_CAL_K = 1.27`. The firmware applies this constant inside the volume calculation in `main.c`; the offline `analysis/scripts/load_run.py` carries the same constant for byte-identical numbers between bench-time LCD output and post-hoc analysis.

Mass-weighted (1.21) and drop-count-weighted (1.17) averages give close but different values; the choice of unweighted mean was deliberate, so that the slow-drip regime (V_50_04, large drops, fewer drops, small mass) gets equal say as the fast-drip regime (V_50_02, small drops, many drops, large mass). The ±30 % residual is the same to first order under any of the three weightings.

## Architecture findings — 2026-05-13 bench

### 1. TOP/BOT optical-channel asymmetry

The two photodiodes report systematically different pulse widths for the same physical drop. Across V_50_01..04 at the original device position with `CAL_MARGIN_HIGH=100`:

| Run | pulse_TOP median (µs) | pulse_BOT median (µs) | BOT/TOP ratio | Physics-expected ratio |
|---|---:|---:|---:|---:|
| V_50_01 | 3896 | 8076 | 2.09× | 0.92× |
| V_50_02 | 3190 | 8013 | 2.50× | 0.92× |
| V_50_03 | 3124 | 5834 | 1.87× | 0.92× |
| V_50_04 | 4680 | 8163 | 1.75× | 0.92× |

The physics prediction comes from gravity acceleration over the 10 mm beam pitch: the drop is travelling ~9 % faster at BOT than at TOP, so its chord-time at BOT should be 9 % **shorter** than at TOP. Bench shows BOT pulses 75–150 % **longer** than TOP. The mean-of-pulses approach in firmware partially absorbs this (BOT over, TOP under → mean roughly tracks truth), but the residual mismatch is one of two drivers of the ±30 % per-run k variance.

### 2. The BOT extension is partially backsplash, partially intrinsic

Falsifiable test on-bench (2026-05-13, ~16:00): the device was repositioned ~3 cm higher on the drip chamber so the BOT beam was further from the pool surface. At the higher position and original thresholds, **the BOT/TOP ratio fell from ~2.0× to ~1.13×** — much closer to physics-expected 0.92×. With thresholds lowered to `CAL_MARGIN_HIGH=30` at the same higher position, the ratio jumped to ~7.8× as the lower threshold caught a long BOT tail invisible at margin=100.

Interpretation: the BOT photodiode sees a real splash-driven tail that the margin=100 threshold clips. Moving the BOT beam further from the pool reduces the tail. Some residual TOP/BOT mismatch persists even at the higher position (1.13× vs 0.92×), so the sensor itself has a small intrinsic asymmetry on top of the backsplash effect.

The current firmware keeps `CAL_MARGIN_HIGH=100` to clip the splash artefact, accepting the residual ~1.2× ratio. A Rev-C optical front-end with the BOT beam moved further from the pool, plus TOP/BOT gain equalisation, would close the gap.

## Drop counting is reliable inside the operating envelope

Inter-drop interval analysis across V_50_01..03 shows tight distributions (p90 < 1.05× median interval), so **the firmware is not missing or doubling chamber drops** in normal flow regimes. The drop **count** is a defensible quantity; only the per-drop volume carries the ±30 % uncertainty.

| Run | Median interval (s) | p90 interval (s) | Gaps > 2× median |
|---|---:|---:|---:|
| V_50_01 | 2.06 | 2.13 | 1 (44.5 s — real drip pause) |
| V_50_02 | 1.63 | 1.72 | 1 (3.4 s — flow micro-stall) |
| V_50_03 | 2.95 | 3.08 | 2 (46.7 s reflash gap; 4.5 s) |

V_50_04 is exempt from this conclusion — it has 15 intervals exceeding 2× the median, including the 248 s mid-run gap.

## Reproducibility

The full chain regenerates byte-identically from a fresh clone:

```powershell
# Acquire bench data (one-time, requires hardware)
python tools\log_uart_run.py capture --port COM3 --rate 50 --run 01 --duration 200 --force
python tools\log_scale.py --port COM4 stream --duration 200 `
  --out data\raw\2026-05-13_macro20_50mlh_01_board1_scale.csv

# Build the overlay figure and the cross-run summary
python tools\build_bench_overlay.py `
  --device-csv data\raw\2026-05-13_macro20_50mlh_01_board1.csv `
  --scale-csv  data\raw\2026-05-13_macro20_50mlh_01_board1_scale.csv `
  --beam-mm 10.2 --density 1.000 --rate-mlh 50

# Sanity-check the firmware k against the offline model
python -c "from analysis.scripts.load_run import load_run, V_CAL_K, summarise_run; print(V_CAL_K)"
```

`analysis/figures/bench_overlay_summary.csv` is the cross-run artefact. Per-run bench notes are in `docs/bench/2026-05-13_V_50_0*.md`. Full limitation inventory in `docs/limitations.md`.
