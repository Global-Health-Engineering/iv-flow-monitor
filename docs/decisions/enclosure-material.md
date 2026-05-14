# Enclosure Material — ASA White, FDM, Snap-Fit Assembly

**Date:** 2026-03-15
**Status:** Accepted
**Decider:** Leandro Catarci

## Context

The Rev-B enclosure must protect the PCB, optics, and battery in a clip-on form factor for clinical use, fabricated at low cost in the 5-unit prototype batch and any subsequent small-volume production. The deployment context is humanitarian healthcare in regions with outdoor light exposure, high ambient temperature, and limited maintenance — UV resistance and warping behaviour during printing matter. The decision combines three coupled sub-decisions: filament material, colour, and fastener mechanism.

## Decision

The enclosure is fabricated by **FDM 3D printing in ASA (Acrylonitrile Styrene Acrylate), white**, with **snap-fit assembly** between body and lid. No threaded fasteners and no heat-set inserts are used.

## Alternatives considered

- **PETG (filament alternative).** Easier to print, similar cost, but lower UV resistance — relevant for outdoor humanitarian deployment, where the device may sit in sun-exposed environments.
- **ABS (filament alternative).** Comparable mechanical properties to ASA, but higher warping risk during FDM printing, especially for large flat surfaces like the back shell.
- **SLA / DLP resin.** Better surface finish than FDM, but higher per-unit cost and a brittle finished part that is less repairable in field conditions.
- **Injection moulding.** Lowest per-unit cost at scale, but tooling cost is not justified at the 5-unit prototype volume; reserved as a Rev-C-or-later option once design is locked.
- **M2 brass heat-set inserts + button-head screws (fastener alternative).** Adds parts, assembly time, and a heat-set installation step. Snap-fits eliminate this in exchange for a printed-geometry-tolerance dependency.

## Consequences

- **UV and weather resistance.** ASA's superior UV stability over PETG and ABS is the central material argument. White colouring further reduces solar heat absorption in high-ambient-temperature settings.
- **Snap-fit assembly.** No screws, no inserts, no separate fasteners to ship with each unit. Assembly time and BOM both reduced. The trade-off is that snap-fit reliability depends on print tolerance — the same FDM ±0.2 mm geometry variability that limits sensor-arm alignment ([`sensor-arm-alignment.md`](sensor-arm-alignment.md)) shows up here too. Disassembly for service requires either flexing the snap-fit lugs or accepting that the enclosure is functionally non-serviceable.
- **Print warping risk reduced (vs ABS).** ASA still requires an enclosed chamber, heated bed (~100 °C), and ~250 °C nozzle, but warping behaviour is more forgiving for the long flat sections in the back shell.
- **Cost.** ASA filament is similar to PETG and ABS per kg (~CHF 30–40), much cheaper than SLA per finished part.

## Outlook (aspirational, not validated for Rev-B)

- **IP54 ingress protection** is a design aspiration for the enclosure form factor — moderate dust intrusion + splash resistance, appropriate for a bedside clinical device. **Rev-B has not been tested against IEC 60529 for IP54 compliance.** The snap-fit joint geometry, optical-bezel sealing, and any cable / button penetrations are unvalidated against ingress. The aspiration is recorded so a Rev-C or follow-up thesis can design and test against it explicitly.

## Revisit triggers

- If the snap-fit reliability proves insufficient in field deployment (lugs failing, repeated open/close cycles loosening the joint), revisit fastener mechanism — heat-set inserts + screws is the natural fallback.
- If a future revision targets actual IEC 60529 IP54 certification, the snap-fit joint geometry, bezel sealing, and button sealing all reopen as design parameters.
- If ASA filament becomes unavailable or significantly more expensive than alternatives, PETG with a UV-stabilised additive is the next option.
- If production scale crosses the threshold where injection-moulding tooling pays back, the FDM-tolerance constraints disappear and the whole material + fastener stack reopens.
