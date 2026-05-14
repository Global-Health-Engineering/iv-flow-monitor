# Testing and Validation — Dripito Rev-B

The validation campaign as it actually ran. The pre-bench protocol document
(EXP-0 → EXP-6 across multiple days) is preserved in this repo's git
history and was compressed into a single bench day. This file documents
what the device was tested against, what was measured, and what was
deliberately left out of scope. Numerical results live in
[`results.md`](results.md); honest weaknesses ranked by impact live in
[`limitations.md`](limitations.md).

## Bench day — 2026-05-13

| Field | Value |
|---|---|
| Date | 2026-05-13 |
| Location | ETH GHE lab, light-controlled |
| Board | 1 (only) |
| Drip set | Macro 20 gtt/mL nominal |
| Fluid | Water, ρ = 1.000 g/mL |
| Beam separation | 10.2 mm (`../data/geometry.json`) |
| Power supply | 3.3 V via ST-Link debugger (boost chain bypassed) |
| Firmware constants (final, applied to all runs) | `BEAM_WIDTH_MM=0.0`, `CAL_MARGIN_HIGH=100`, `CAL_MARGIN_LOW=30`, `D_MM_MIN=0.1`, `V_CAL_K=1.27` |
| Ground truth | Mettler-Toledo MS-series precision scale (±0.0001 g) streaming SICS `SIR` at ~23 Hz |

The firmware constants above are the **final** values committed to
`firmware/STM32CubeIDE/InfusionBA2/`. Constants were tuned during the
morning calibration runs (V_50_01..04); the calibrated value
`V_CAL_K = 1.27` was baked in and verified against the independent run
V_50_05. The full in-bench change log is in `limitations.md` §14.

## Ground truth — per-run chamber-orifice gravimetric

The device counts drops at the **drip-chamber orifice** (where they form).
The scale captures mass at the **end-of-tubing orifice** (where they fall
into the catch vessel). These two orifices have different geometry, so
they drip at different rates with different drop sizes — see
`limitations.md` §2.

Mass conservation still holds:

```
N_chamber × V_chamber  =  N_end × V_end  =  total mass through tubing
```

so the **only valid pairing** between the device's per-drop output and
the scale at the per-drop level is the per-run average:

```
V_true_chamber  =  total_mass_g × 1000 / N_UART_chamber_drops   (µL/drop)
```

Per-drop matching of UART events to scale steps is preserved as an
exploratory diagnostic only (`tools/match_scale_drops.py`; the docstring
documents the invalidation).

## Morning — calibration + verification runs

Five 3–10 minute runs at a clamp setting nominally 50 mL/hr (actual flow
varied; ground truth anchors on the gravimetric, not the clamp). Each run
produced three files in `../data/raw/`:

```
2026-05-13_macro20_50mlh_<NN>_board1.csv           # firmware DROP rows (12-col UART)
2026-05-13_macro20_50mlh_<NN>_board1.log           # raw UART mirror (audit trail)
2026-05-13_macro20_50mlh_<NN>_board1_scale.csv     # scale SIR stream
```

Per-run notes:

| Run | Detail file |
|-----|-------------|
| V_50_01 | [`bench/2026-05-13_V_50_01.md`](bench/2026-05-13_V_50_01.md) |
| V_50_02 | [`bench/2026-05-13_V_50_02.md`](bench/2026-05-13_V_50_02.md) |
| V_50_03 | [`bench/2026-05-13_V_50_03.md`](bench/2026-05-13_V_50_03.md) |
| V_50_04 | [`bench/2026-05-13_V_50_04.md`](bench/2026-05-13_V_50_04.md) |
| V_50_05 | [`bench/2026-05-13_V_50_05.md`](bench/2026-05-13_V_50_05.md) |
| V_streaming | [`bench/2026-05-13_V_streaming.md`](bench/2026-05-13_V_streaming.md) |

Headline numbers (per-run V_true_chamber, V_est, k_post, residuals) are
tabulated in [`results.md`](results.md). The summary: after applying
`V_CAL_K = 1.27`, the device tracks the gravimetric per-chamber-drop
average to within ±30 % across the operating envelope.

`V_CAL_K = 1.27` is the unweighted mean of `k_pre` across V_50_01..04
(see `results.md` for the derivation table). Reporting per-run residual
against the same four runs is a self-consistency check, not an
independent validation. V_50_05 — captured after baking `V_CAL_K` into
firmware — is the independent verification.

## Afternoon — mount-height re-test (position-drift)

A second session on the afternoon of 2026-05-13 mounted the device at
three different heights on the same drip chamber, same drip set, same
fluid, same board, and measured the K required to make the LCD-summed
drop volume match the gravimetric reading at that position.

**Finding: K varied from 0.28 to 1.27 across positions — a 4.5× range
driven by mount geometry alone.** Three position-dependent contaminants
of the chord measurement were isolated (umbilical at TOP, backsplash at
BOT, threshold-vs-peak mismatch at the dual-threshold core pulse). No
single (algorithm, K) combination passed ±5 % at all positions.

Full architectural analysis: `limitations.md` §17.

Raw afternoon runs live in `../data/raw/2026-05-13_pm_position_drift/`
with a per-run README inside the folder documenting each mount position
and the K required.

The Rev-B firmware was reverted to the morning-calibrated
`V_CAL_K = 1.27` mean-pulse state at the end of the afternoon session.
The position-dependence finding is documented as a §17 architectural
limit; the V_50 headline in `results.md` is left untouched.

## What was deliberately not in scope

| Out of scope (Rev-B) | Why | Where it's named |
|----------------------|-----|------------------|
| Rev-A baseline (count-only firmware) | Earlier InfusionBA was removed in commit `ed84ff5`; recovering it for a head-to-head was infeasible in the project timeline | `limitations.md` §12 |
| Multiple drip sets | Single macro 20 gtt/mL available on bench | `limitations.md` §10 |
| Multiple boards | Single board built; board-to-board scatter from the printed sensor arm is un-quantified | `limitations.md` §8, §16 |
| Multiple head heights | Single head height; clinical range 60–150 cm not covered | `limitations.md` §13 |
| Battery-powered runs | Tethered 3.3 V via ST-Link; TPS610981 boost chain not in the validated loop | `limitations.md` §7 |
| Multi-session generalisation | Single bench day; drift across sessions un-quantified | `limitations.md` §15 |

## Data + analysis cross-links

- Raw CSVs: `../data/raw/` — see [`../data/README.md`](../data/README.md) for column schemas.
- Per-run gravimetric summary: `../data/gravimetric_log.csv`.
- Geometry: `../data/geometry.json`.
- Analysis pipeline: [`../analysis/`](../analysis/) — `docker compose up regenerate-figures-sample` regenerates the headline figure from sample data.
- Headline results: [`results.md`](results.md).

## Archive / Zenodo

The complete dataset (raw CSVs, gravimetric log, per-drop summaries,
analysis pipeline) will be deposited on Zenodo under CC BY 4.0. DOI:
*10.5281/zenodo.TBD — minted post-submission*.
