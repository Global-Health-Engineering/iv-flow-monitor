# Optical Architecture — Dual-Beam Phase 1 + LPTIM1 Single-Beam Phase 2

**Date:** 2026-03-15

## Context

Rev-A used a continuous single-beam optical drop detector with a fixed assumed drop volume (50 µL for macro 20 gtt/mL drip sets). This fixed-volume assumption was the dominant source of flow-rate error in Rev-A, because real drop volumes vary with drip-set geometry, fluid surface tension, and drip rate (Tate's-Law dependence). Rev-B has two design constraints that drove the optical-architecture decision: (1) the system must accept any standard macro/micro/neonatal drip set without manual configuration, and (2) the device must run on a single Li-ion AA for multi-week sessions (see [`power-architecture.md`](power-architecture.md)), forcing aggressive duty-cycling of the IR emitters.

## Decision

The Rev-B optical chain uses a two-phase approach:

- **Phase 1 — calibration (first ~10 drops after boot).** Both IR beams (TOP and BOT, 10 mm vertical separation) run simultaneously. Per drop, the firmware measures transit time between the two beam crossings and pulse width on each beam to infer drop volume from a sphere-model chord-time calculation. This delivers a per-session, drip-set-agnostic empirical drop volume tied to the actual fluid and chamber in use.
- **Phase 2 — continuous monitoring.** Once Phase 1 has converged on a stable volume estimate, the device switches to single-LED operation. LPTIM1 drives a low-duty pulse train on the BOT beam; the internal COMP1 wakes the MCU on each drop crossing. The TOP beam is unused in Phase 2. This gates the IR LED average current to ~57 µA (0.3 % duty at 19 mA peak), enabling the multi-week runtime target.

## Alternatives considered

- **Rev-A approach — single-beam continuous, fixed assumed drop volume.** Lost on accuracy: the fixed 50 µL/drop assumption is the dominant Rev-A error term, and any device claiming flow-rate measurement across drip sets must measure (not assume) drop volume.
- **External ADC sampling against firmware threshold (no internal comparator).** Lost on power: continuous ADC sampling consumes more average current than the comparator-on-wake-up architecture, and the ADC dynamic range is wasted on what is fundamentally a one-bit transit event.
- **Permanent dual-beam continuous operation.** Lost on power: running both IR LEDs continuously at the duty cycle Phase 1 needs would prevent multi-week runtime on a single AA. The dual-beam phase is the price paid for per-session calibration; minimising its duration (~10 drops) keeps the energy cost bounded.

## Consequences

- **Drip-set-agnostic.** The user does not configure a drip-set type. The device measures it. This is the central UX simplification vs Rev-A and the dominant accuracy lever.
- **Calibration is per-session, not per-device.** Every boot re-runs Phase 1. This is robust against drip-set swaps and fluid changes mid-deployment without firmware support for explicit recalibration.
- **Target architectural accuracy ceiling: ~4–5 % systematic error.** This was the pre-bench prediction, vs Rev-A's ~10 %. As of the 2026-05-13 bench, the current Rev-B firmware + sensor-arm geometry achieves a residual of ±30 % per-run on the morning V_50 campaign (see [`../results.md`](../results.md)), dominated by drop-shape oscillation between oblate and prolate during free fall (see [`../limitations.md`](../limitations.md) §Drop-shape oscillation and §Position-dependence). The architectural ceiling of 4–5 % remains the design target; closing the gap to it requires algorithm rework on the chord-time estimator and likely a sensor-arm geometry that better controls drop trajectory through the beams. Whether the architectural ceiling is actually reachable in the Rev-B form-factor is open, and further bench iteration is needed to bound the achievable accuracy.
- **The Phase 1 / Phase 2 split couples firmware complexity to a transition trigger.** Phase 2 entry requires a stable Phase-1 estimate and depends on calibration convergence within the first ~10 drops; pathological drip-rate or geometry conditions can stall the transition. Documented as an open firmware path in [`auto-calibration-at-boot.md`](auto-calibration-at-boot.md).
- **Dual-LED layout buys a fault-tolerance side-benefit.** If one IR LED fails in field deployment, the firmware can fall back to single-beam operation on the surviving emitter — at the cost of Phase-1 calibration accuracy, but with the device still functional as a Rev-A-style counter. Not a design driver; recorded as a consequence worth keeping.

## Revisit triggers

- If bench iteration shows the chord-time architecture cannot close the gap from ±30 % to ~5 % even with algorithm rework + geometry control, the optical architecture itself reopens. Candidate replacements include horizontally-separated beams (resolves the sphere-from-vertical-chord ambiguity that drop oscillation creates) and TOP/BOT gain equalisation (see [`../limitations.md`](../limitations.md) §Position-dependence).
- If the Phase 1 / Phase 2 transition logic proves unreliable in field deployment, revisit the convergence criteria or merge to a single continuously-calibrating mode.
- If a future revision drops the dual-LED layout (e.g. for cost), the fault-tolerance consequence above is forfeited.
