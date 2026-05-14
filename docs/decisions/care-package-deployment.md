# Dripito Care Package — Planned Deployment Model (Not Executed)

**Date:** 2026-03-26 (initial framing)

> **This ADR documents a planned deployment model, not a built deliverable.** The Care Package is the deployment-context surround for the cell-chemistry decision in [`power-architecture.md`](power-architecture.md). No Rev-B unit has shipped with this kit; the model exists as a target for Rev-C field trials and as input to manufacturing / logistics planning.

## Context

The [Rev-B power architecture](power-architecture.md) chose the single Li-ion AA cell over the 18650 partly on field-deployment grounds: surge resilience (no on-PCB charging), field repairability (replaceable cell), and alkaline-AA fallback when the rechargeable cell or its charging infrastructure is unavailable. These arguments only deliver their value if the deployment context actually provides the alkaline cells and the charging infrastructure that the architecture assumes. The Care Package is the deployment-side complement that turns the cell-chemistry decision into a deployable system.

The Care Package framing emerged from the Tupesis consultation (see [`power-architecture-process.md`](power-architecture-process.md) §3 — Field power quality is dangerous; small devices with dead internal batteries get discarded; AA availability is ubiquitous in normal LMIC contexts but scarce in acute emergencies).

## Decision

**Planned content of one Dripito Care Package** (for a field hospital with 3–5 deployed devices, depending on facility size):

- **Dripito units** with rechargeable Li-ion AA installed (primary).
- **Alkaline AA batteries**, in a quantity equal to or greater than the Dripito count. Field-replaceable fallback when the rechargeable cell is dead and no charging is available; turns the device into a consumable rather than a brick.
- **Portable USB solar panel** — 5 V, 2 W, 400 mA. **External** charging, plugged into the AA cell's USB-C port. The AA charges from the panel; the device electronics never see the panel.
- **USB-C cable** for connecting the panel to the AA cell.

The decisive feature is that solar charging happens **externally** to the device — the AA cell sits in the panel's output, not on the device PCB. This avoids the thermal-safety problem of charging a Li-ion cell inside an enclosure that can reach 60–80 °C in direct equatorial sun (see [`power-architecture-process.md`](power-architecture-process.md) §5 — Solar Trickle Charging Feasibility).

## Why this model

- **Solar without thermal risk.** PCB-mounted solar harvesting was rejected in `power-architecture.md` on thermal-safety + AA-architecture-compatibility grounds. External solar via the AA's own USB-C port keeps the charging-temperature constraint outside the device.
- **Alkaline fallback for acute emergencies.** Tupesis's evidence is that in acute humanitarian crises (e.g. Gaza), even normally-ubiquitous batteries become scarce. The Care Package ships its own redundancy.
- **No sealed internal battery to fail.** Reinforces the field-repairability argument in `power-architecture.md`. A failed cell is a swap, not a discarded device.
- **Multi-device packaging amortises shipping + logistics cost.** A field hospital does not receive one device; it receives a deployment kit.

## Alternatives considered

- **Ship Rev-B devices alone, no kit.** The cell-chemistry decision still works on its own merits (surge resilience, alkaline fallback in principle), but the surrounding logistics (where the alkaline cells come from, how the rechargeable cell is charged) are left as a problem for the receiving facility. Rejected: the Tupesis evidence is that field infrastructure cannot be relied on to provide these.
- **Bundle each device with charging hardware, no spare AAs.** Misses the acute-emergency case where charging infrastructure fails.
- **Internal solar panel on the device.** Rejected on thermal-safety grounds — see `power-architecture-process.md` §5.

## Consequences

- **The deployment cost per facility is larger than per-device.** Solar panel + cable + alkaline batteries are real per-deployment line items.
- **The deployment logistics are not trivial.** A working field deployment of the Care Package requires sourcing the solar panel (well-validated 5 V 2 W panels exist but are not on the BOM), the USB-C cable, and a sufficient quantity of alkaline AAs locally or via the deployment.
- **Rev-B has not validated this model.** No Care Package has been packaged, shipped, or used. The architecture is consistent with this deployment model; the deployment itself is future work.

## Open questions for Rev-C / field trial

- **Solar panel selection** — concrete part choice, ruggedness specification, mounting / storage in the kit packaging.
- **Alkaline AA quantity per kit** — depends on rechargeable-cell cycle life and field-charging availability. No data yet.
- **Field-hospital sizing rule** — 3–5 units per facility is a starting estimate; actual ward count + IV-line load is needed to size properly.
- **Documentation / training material** — clinicians need to know what each kit component is for. Out of scope for Rev-B.

## Revisit triggers

- **Rev-C field trial** is the natural revisit point. The Care Package model becomes a concrete logistics + manufacturing question once units are being prepared for deployment.
- If a Rev-C power architecture moves away from the removable Li-ion AA (e.g. to 18650 or LiPo), the entire Care Package model reopens — the "external charging only" feature depends on the AA architecture.
- If field experience with deployed Rev-C units shows that the alkaline fallback is rarely used or that solar panels go unused, the kit composition simplifies.
