# Threshold Auto-Calibration at Boot

**Date:** 2026-05-04 (architecture); finalised as primary path during 2026-05-13 campaign

## Context

The Rev-B [optical front-end](optical-architecture.md) uses internal COMP1 thresholded against a DAC reference to detect drop events. The threshold value depends on (a) the baseline illumination delivered by the IR LED to each photodiode in the assembled device, and (b) the drop-shadow depth, which depends on chamber OD, fluid optical properties, and beam alignment. These quantities vary across boards (FDM tolerance, see [`sensor-arm-alignment.md`](sensor-arm-alignment.md)), across drip-set / fluid combinations, and across ambient illumination conditions. A fixed compile-time threshold cannot stay correct across this variation; some form of per-boot adaptation is needed.

## Decision

The firmware **auto-calibrates the COMP1 detection thresholds at every boot** by sweeping the IR LEDs against the photodiode baseline, measuring the baseline and the in-shadow minimum, and computing per-beam threshold values from that pair. No compile-time `#define` threshold is retained as a fallback — auto-cal is the **sole** threshold source in Rev-B.

The auto-cal output (baseline, in-shadow minimum, computed threshold per beam, timestamp, board ID) is streamed over UART and written to `data/calibration_log.csv` for every session so threshold history is reproducible from the data record.

## Alternatives considered

- **Pure manual hard-coded `#define` thresholds (no auto-cal).** Rejected: cannot stay correct across board-to-board variation, drip-set changes, or ambient illumination changes without manual recompile. Reproducibility-of-data argument that originally favoured this path (fixed threshold = no per-boot drift) is outweighed by the operational fragility — a fixed threshold gives the wrong answer the moment the device is moved or the chamber changes.
- **Hybrid (auto-cal as primary, `#define` as fallback if auto-cal sanity check fails).** Was the architecture proposed in the 2026-05-04 planning note. Rejected for Rev-B because it doubles the firmware paths the validation campaign has to characterise; the auto-cal path can be made robust enough on its own, and a fallback would mask auto-cal failures during validation. The fallback path is reintroducible in Rev-C if auto-cal proves unreliable in field deployment.
- **Per-session manual recalibration triggered by the user.** Rejected on UX grounds: clinicians should not be expected to perform a calibration step before each use. The boot-time auto-cal is the per-session calibration.

## Consequences

- **Per-board, per-session adaptive thresholds.** The device adapts to its own LED current, photodiode placement, sensor-arm geometry, and ambient illumination on every boot, without any user input.
- **Threshold history is in the data record.** Every session's auto-cal output is logged to `calibration_log.csv`. The validation analysis (`docs/results.md`) can be cross-referenced against the per-session thresholds.
- **Silent auto-cal failure is a real risk.** If auto-cal converges on a bad threshold (misaligned beam, low LED current at boot, bubble in chamber during sweep, ambient light spike, threshold-vs-peak boot-cal drift — see [`../limitations.md`](../limitations.md) §Position-dependence), the device runs with incorrect thresholds and the run looks normal until post-hoc analysis catches it. Bench evidence from the 2026-05-13 campaign shows this happens — the boot-cal baseline shifts 100–200 counts between sessions and the fixed-margin core threshold cuts at a different fraction of (peak − baseline) per boot, contributing to the per-run residual.
- **No `#define` rescue path if auto-cal breaks.** A firmware build with a fundamental auto-cal bug bricks the device for the user. Mitigation in Rev-B is to surface auto-cal output via UART so a failure is observable on-bench; not a user-facing mitigation.

## Revisit triggers

- If field deployment shows auto-cal failure modes that cannot be made observable from inside the device (no UART, no logs accessible), reintroduce a `#define` fallback or add explicit on-LCD diagnostic output.
- If the boot-cal baseline drift documented in [`../limitations.md`](../limitations.md) §Position-dependence is shown to materially degrade accuracy and cannot be fixed by algorithm rework in the chord-time estimator, the auto-cal sanity-check criteria become a load-bearing part of the optical architecture and may need rework.
- If Rev-C uses a different optical front-end (e.g. analog continuous sampling, different photodiode), the entire calibration approach reopens.
