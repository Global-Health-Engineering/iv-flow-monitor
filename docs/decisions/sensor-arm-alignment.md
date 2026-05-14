# Sensor Arm Alignment — FDM in Rev-B, Injection Moulding Pathway

**Date:** 2026-03-15 (initial); 2026-05-01 (Rev-B implementation decision)
**Status:** Accepted (Rev-B FDM); injection moulding identified as Rev-C / production-scale path
**Decider:** Leandro Catarci

## Context

The Rev-B [optical architecture](optical-architecture.md) uses a dual-beam phase-1 calibration where the geometric chord time through both IR beams is converted into a drop volume. The chord-time calculation is directly sensitive to the **beam separation distance** and the **alignment of the two beams to a common drop trajectory**. Any unit-to-unit variation in the beam positions on the sensor arm therefore translates directly into per-unit calibration error and, downstream, flow-rate error.

FDM-printed geometry typically holds ±0.2 mm tolerance on positional features. With a nominal 10 mm beam separation, that is ±2 % geometric variation per unit — non-trivial fraction of the architectural accuracy budget (see [`optical-architecture.md`](optical-architecture.md)).

## Decision

**Rev-B:** Direct FDM-printed sensor-arm geometry, no additional alignment hardware. The IR LEDs and photodiodes are mounted into printed bores in the sensor arm; the arm geometry itself is the alignment reference. Alignment precision is bounded by FDM tolerance (±0.2 mm typical for ASA on a calibrated printer).

**Rev-C / production scale:** Migrate the sensor arm from FDM to **injection-moulded ASA**. Injection moulding typically delivers ±0.05 mm positional tolerance on small features — a ~4× improvement over FDM — and improves with mould quality, gate placement, and process control. At production volume the tooling cost is amortised, the per-unit cost drops, and the alignment precision improves enough that the dual-beam chord-time architecture's geometric error contribution becomes a small fraction of the per-drop residual rather than a significant one.

## Alternatives considered

- **Printed alignment ribs / inserts (FDM, Rev-B baseline).** What Rev-B uses. Easy to print, no extra parts, FDM-bound tolerance.
- **Adhesive bonding the beam emitter / receiver assembly into the arm.** Removes the printed-geometry tolerance dependency in exchange for a non-reversible assembly step and an adhesive failure mode under field temperature swings.
- **Per-unit calibration of the geometric constant in firmware.** Replaces a mechanical fix with a software one: measure each unit's beam separation at assembly and burn it into firmware. Works, but introduces a per-unit assembly + calibration step incompatible with the design goal of identical drop-in production units.
- **Production technologies other than injection moulding** (SLA, DMLS, CNC). Discussed only briefly: SLA has UV-aging concerns for the long-deployment context; DMLS / CNC are uneconomic for a small polymer part at this volume.

## Consequences

- **Rev-B alignment precision is FDM-bound.** Any inter-unit variation in beam separation contributes directly to calibration scatter in the validation data, and is one of the named sources of per-board geometry variation in the a priori MC error budget (see [`../limitations.md`](../limitations.md) §Print-tolerance dominance is predicted but not refuted).
- **The current Rev-B sensor arm is not the final mechanical design.** A full rework is expected for a production-grade device. The Rev-B arm exists to integrate the optics + chamber holder + electronics into a single testable assembly, not to deliver target accuracy.
- **The Rev-C path is a process change (FDM → injection moulding), not a part-count change.** No new alignment hardware is introduced. The same geometric reference (printed bores in the arm) becomes a moulded reference with better tolerance.

## Revisit triggers

- If a Rev-B unit fails calibration-scatter targets specifically because of beam-separation variance, treat the FDM arm as the near-term blocker and either move to a per-unit firmware calibration step or accelerate the move to moulded parts for the validation fleet.
- If production scale never materialises (i.e. the device stays in prototype / small-batch FDM territory), revisit the alignment-precision strategy on its own terms — per-unit firmware calibration is then the most plausible alternative.
- If a different sensor-arm geometry (different beam separation, different chamber-OD scope, different optical layout) becomes necessary, bundle the production-tooling decision into that rework cycle rather than treating it as a separate step.
