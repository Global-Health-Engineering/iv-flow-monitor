# COMP1 Simplification — Remove External LMV331, Use STM32G071 Internal Comparator

**Date:** 2026-03-12
**Status:** Accepted
**Decider:** Leandro Catarci

## Context

The Rev-A reference design (Fionn Smith) used an external LMV331 single-channel comparator to threshold the photodiode signal into a clean digital drop-detection edge for the MCU. Rev-B targets the STM32G071C8TX, which exposes one internal comparator peripheral (COMP1) with a programmable reference via the internal DAC and a deterministic propagation time in the sub-microsecond range — well below the millisecond-scale drop transit window. Keeping the external LMV331 would have added a part, a BOM line, and three passives without obvious gain over the on-chip alternative.

## Decision

The external LMV331 comparator was removed from the Rev-B schematic. The photodiode signal is thresholded by the STM32G071's internal COMP1 peripheral using the internal reference DAC for the threshold voltage.

## Alternatives considered

- **External LMV331 (Rev-A heritage).** Lost on BOM count, board area, and the fact that the on-chip COMP1 meets the speed and threshold-configurability requirements without compromise.
- **External TLV3201 (faster external comparator).** Lower propagation delay than LMV331, but the speed margin already provided by COMP1 over the drop-detection time scale makes the upgrade pointless.

## Consequences

- One IC and ~3 passives removed from the BOM. Lower component count, smaller PCB area for the analog front-end, simpler procurement.
- Threshold and hysteresis configurability moved from external resistor network to firmware (DAC code + COMP1 hysteresis bits). This is more flexible (per-board threshold without rework) but couples the analog signal chain to firmware correctness.
- The simplification was identified during schematic review without prompting from the supervisor. Documented here as evidence of independent design initiative beyond the inherited Rev-A reference.

## Revisit triggers

- If bench measurement shows COMP1's input offset voltage or hysteresis is inadequate against the photodiode noise floor at low illumination, revisit by either tuning DAC threshold + hysteresis bits or restoring an external comparator. (Open as of 2026-03-12; to be validated during Rev-B bring-up.)
- If a future revision moves to a different MCU family without an on-chip comparator suitable for this task, the LMV331/TLV3201 path becomes the natural fallback.
