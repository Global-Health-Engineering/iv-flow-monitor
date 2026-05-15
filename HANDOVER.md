# Handover — Dripito Rev-B → Rev-C

State of the project at submission (2026-05-14) and what the next person
working on this device needs to know to pick it up.

## What Rev-B is

A single-board, single-AA-cell prototype IV drip flow-rate monitor with
dual-beam optical drop detection on an STM32G071C8. The device counts
drops at the **drip-chamber orifice**, times them across two
horizontally-aligned IR beams (10.2 mm separation), and reports
per-drop volume + cumulative flow on a 4×16 LCD. Submitted as an ETH GHE
MSc semester project; **not a certified medical device.**

What's reproducible:

- `docker compose up regenerate-figures-sample` in `analysis/` cold-builds
  the headline figure on a clean machine.
- The 2026-05-13 bench dataset (`data/raw/2026-05-13_*`) is committed,
  documented in `data/README.md` with explicit column schemas, and
  re-analysable from the included pipeline.
- The hardware is fully spec'd: KiCad 8 project, BOM-CSV, gerbers, three
  custom footprints under CC BY-SA 4.0.

## What works (within Rev-B scope)

- **Optical detection chain.** Both beams reliably trigger on individual
  drops at the morning calibration mount position. Drop counting matches
  the gravimetric drop count to within a few percent over a 3-10 minute
  run at that position.
- **Sphere-model volume estimate after calibration.** Post-`V_CAL_K=1.27`
  per-run residual against gravimetric is ±30 % across the operating
  envelope on V_50_01..05.
- **Velocity (transit time) is position-agnostic.** The two beams deliver
  reliable time-of-flight regardless of mount height.
- **Reproducible build + analysis.** STM32CubeIDE GUI builds the firmware;
  the Docker pipeline regenerates results on any machine.

## What does not work (Rev-B's three blockers)

1. **Position-dependent chord measurement (§17 of `docs/limitations.md`).**
   The 2026-05-13 afternoon session measured the K required to make the
   LCD-summed drop volume match gravimetric at four mount positions on
   the same drip chamber. With the shipped mean-of-pulses algorithm,
   K_fit ranged 0.42–1.27 across positions (3× spread); across all eight
   algorithm variants trialled, K_fit spanned 0.42–1.98 (4.7× spread
   driven by mount geometry alone). Three contaminants isolated:
   *umbilical at TOP* (filament still attached when drop crosses TOP
   beam), *backsplash at BOT* (splash particles cross BOT beam after the
   drop body has cleared), *threshold-vs-peak mismatch* on the dual-
   threshold core pulse. **No (algorithm, K) combination passed ±5 % at
   all positions.**
2. **Drop oscillation between oblate and prolate shapes** in the first
   10–30 mm of free fall. The beam plane catches each drop at an
   unpredictable point in the oscillation. Mean averages out (hence
   `V_CAL_K` works on the run mean); per-drop CV stays inflated.
3. **Tilt sensitivity, un-quantified.** Sub-mm chamber reposition doubled
   TOP pulse width on bench. The chord-time architecture is sensitive to
   off-vertical drop trajectories.

## Rev-C path (named throughout `docs/limitations.md`)

The Rev-C optical front-end has to deliver position-invariant chord
measurement, not just position-invariant counting:

- **Second beam pair, horizontally offset.** Catches the horizontal
  extent of each drop. With vertical + horizontal extent, the firmware
  can infer the oscillation phase and apply an oscillation-aware
  volume formula instead of sphere-from-vertical-chord.
- **Wider TOP-to-BOT separation.** Drops fully detach from the chamber
  tip before reaching the TOP beam — kills the umbilical contaminant.
- **TOP beam further from the pool surface or shielded against splash.**
  Kills the backsplash contaminant at high mounts.
- **TOP/BOT gain equalisation.** Removes the per-board dynamic-range
  scatter that breaks fixed-margin core thresholds.
- **Mechanical: verticality budget on the chamber holder.** The
  improvised broom-clip Rev-B holder is bench-grade. Rev-C needs a
  printed clamp with a stated tolerance.
- **Power: validate the TPS610981 boost chain.** Rev-B was tethered to
  3.3 V via ST-Link; the single-AA loop was never validated end-to-end.

`docs/decisions/firmware-build-and-test-rev-c.md` is the ADR for the
deferred firmware-CI work (Dockerfile + Makefile, host-buildable Unity
harness for the drop-detection state machine). Both were skipped for
Rev-B to avoid regression risk to the bench-validated firmware in the
final 4-day window before submission.

## Where things live

| Area | Path |
|---|---|
| Firmware (Rev-B) | `firmware/STM32CubeIDE/Dripito/` |
| Hardware (KiCad 8) | `hardware/flow_monitor.kicad_sch`, `.kicad_pcb` |
| Enclosure (ASA print) | `enclosure/` |
| Validation dataset | `data/raw/2026-05-13_*`, `data/raw/2026-05-14_pm/` |
| Analysis pipeline | `analysis/` (docker-composed) |
| Architecture Decision Records | `docs/decisions/` |
| Known limits, ranked by impact | `docs/limitations.md` |
| Headline results | `docs/results.md` |
| Validation protocol | `docs/testing-and-validation.md` |
| Bench tooling | `tools/` (UART/scale loggers, figure builders) |

## Open experiments (not run for Rev-B)

- **Rev-A baseline** (count-only firmware on STM32G030, commit `ed84ff5`)
  was removed before bench day; a head-to-head against fixed-factor
  literature methods is the obvious paper-grade comparison.
- **Multi-board scatter.** n=1 board for geometry. The print-tolerance
  MC error budget predicts 49 % of MAPE from per-board sensor-arm
  geometry; not refuted.
- **Multiple drip sets.** Single macro-20 set on bench; macro-15, macro-10,
  micro-60 untested.
- **Multiple head heights.** Single drip-chamber-to-TOP-beam height; clinical
  range 60–150 cm uncovered.
- **Multi-session generalisation.** Single bench day; session-to-session
  drift un-quantified.

## Reproducing the bench day

The full 2026-05-13 protocol-as-run is in
`docs/testing-and-validation.md`. The morning calibration runs (V_50_01..04)
fit `V_CAL_K`; V_50_05 is the independent verification with K baked into
firmware. The afternoon position-drift runs are in a separate
`data/raw/2026-05-13_pm_position_drift/` folder with a per-run README
documenting each mount position and the K required at that position.

## Contact

Leandro Catarci · `lcatarci@ethz.ch` · ETH MSc, D-MAVT, Global Health
Engineering. Bachelor thesis baseline:
[10.5281/zenodo.16902366](https://doi.org/10.5281/zenodo.16902366).
Rev-B archive DOI: [10.5281/zenodo.20199232](https://doi.org/10.5281/zenodo.20199232).
