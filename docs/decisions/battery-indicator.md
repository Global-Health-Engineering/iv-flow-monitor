# Battery Indicator — Low-Battery Symbol via Threshold (Deferred to Rev-C)

**Date:** 2026-03-27
**Status:** Proposed (deferred to Rev-C; Rev-B firmware has no battery indicator)
**Decider:** Leandro Catarci

## Context

The Rev-B 4×16 LCD displays the live drop count and computed flow rate at all times during clinical operation. A battery state-of-charge indicator would let the user know when to swap the AA cell (see [`power-architecture.md`](power-architecture.md)) — but adding a granular indicator is constrained by both the cell chemistry's discharge curve and the LCD's information budget.

## Decision

**Rev-B firmware has no battery indicator.** The decision below documents the planned design for Rev-C; no implementation work was done in Rev-B.

**Planned design (Rev-C):** A single low-battery symbol on the LCD, triggered by an ADC threshold on the cell voltage. No numeric percentage display. The threshold-flag approach replaces the originally-considered percentage readout because the Paleblue Li-ion AA's discharge curve is flat (~1.5 V across the usable capacity), so a single-ADC-reading percentage interpolation would be either always "100 %" or suddenly "0 %" — worse than no indicator.

## Alternatives considered

- **Battery percentage on LCD (numeric).** Rejected: flat Li-ion AA discharge curve has no meaningful voltage-to-SOC mapping from a single ADC reading. Would require a lookup table per chemistry + temperature compensation, out of scope for a single-cell-chemistry device.
- **Raw voltage readout (ADC value).** Rejected on UX grounds: clinicians do not act on raw voltage, only on the swap-or-don't decision.
- **No indicator at all.** What Rev-B currently ships. The user has no on-device feedback about cell state. Acceptable for a prototype validation campaign but not for clinical deployment.

## Planned implementation (Rev-C)

- ADC reads battery voltage via `ADC_V_BAT` connected to the `BST_VIN` node (after the R8 330 Ω + C4 100 nF filter already on the PCB; no additional components needed).
- Firmware samples periodically, applies software averaging across multiple readings.
- Trigger the low-battery symbol when averaged VBAT drops below ~1.35 V at the TPS610981 input.
- Hysteresis above the threshold to prevent flicker as the cell sags under transient load.

## Consequences

- **Rev-B users have no on-device cell-state feedback.** During bench validation this is fine (the user can monitor cell voltage on a multimeter). For any clinical-context deployment, the indicator becomes a usability requirement.
- **The hardware path is ready.** The ADC + filter network is already on the PCB; the only work needed in Rev-C is firmware (ADC sampling, threshold logic, LCD symbol).
- **If the cell chemistry ever changes to alkaline AA only,** a percentage display becomes interpolable from the alkaline discharge curve — that ADR reopens then.

## Revisit triggers

- **Rev-C firmware** is the natural revisit point. The hardware is in place; the firmware change is bounded.
- If a clinical deployment is attempted with Rev-B firmware (without battery indicator), the indicator becomes a hard blocker and gets prioritised.
- If the cell chemistry changes, the indicator strategy (threshold vs percentage) reopens.
