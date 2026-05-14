# Chamber Holder Mechanism — Sliding Gear with Beam Pass-Through

**Date:** 2026-04-28 (initial direction); 2026-05 (Rev-B implementation)
**Status:** Accepted (Rev-B); Rev-C rework expected
**Decider:** Leandro Catarci

## Context

The drip chamber needs to be held in a fixed, repeatable position relative to the IR beams so the optical signal path passes through the falling drop trajectory. Drip chambers vary in OD across drip-set vendors — Rev-B targets 14–24 mm covering microdrip + adult macrodrip ([`../enclosure-requirements.md`](../enclosure-requirements.md)).

## Decision

Rev-B uses a **sliding gear** as the chamber holder. The gear translates against the chamber to grip it, with a **hole through the gear body** so the IR beam can pass through to the chamber. The detector sits on the opposite side, with the gear + chamber in the optical path.

This is the executed Rev-B implementation, not the optimal mechanism — it integrates the chamber + holder + optical path into a testable subassembly so the rest of the device (PCB, firmware, calibration) can be validated. **A full rework is expected for Rev-C.**

## Known limitations

- **Beam-to-sensor distance is large.** The pass-through hole forces a wide air gap between IR LED and photodiode, reducing signal level and increasing ambient stray-light sensitivity.
- **Hole geometry is fixed; chamber OD variation shifts beam-to-drop alignment.** A 14 mm chamber sits differently than a 24 mm chamber.
- **Mechanism is single-DOF (sliding only).** No independent control over chamber centring or angular orientation.

## Alternatives considered

- **Hinged clamshell cradle.** A separate-piece lid pivoting open to admit the chamber. Higher part count and a closure-latch / hinge-axis design problem; not pursued for Rev-B.
- **Threaded compression collar.** Manual screw to grip. Slow to use, not clinician-friendly.
- **Flexible split-cylinder snap-fit (single OD).** Fails the 14–24 mm OD scope requirement.

## Consequences

- **Validation data was collected with this geometry.** The accuracy numbers in [`../results.md`](../results.md) and the position-dependence finding in [`../limitations.md`](../limitations.md) §Position-dependence reflect the sliding-gear optical path, not the eventual Rev-C mechanism.
- **The wide beam-to-sensor distance contributes to position-dependence.** The umbilical-at-TOP and splash-at-BOT regimes in §17 of limitations are partly artefacts of this geometry. A tighter beam-to-chamber path in Rev-C should reduce both contaminants.

## Revisit triggers

- **Rev-C is the expected revisit point.** The holder is a named Rev-C rework item.
- If Rev-B residuals are shown to be dominated by holder-geometry artefacts (drop trajectory through beam, ambient stray light, OD-dependent alignment shift), the rework moves earlier.
- If chamber OD scope changes (e.g. wide-body 25–30 mm), the gear-jaw range no longer covers the scope.
