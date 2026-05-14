# Power Architecture — Single Li-ion AA via TPS610981 Boost

**Date:** 2026-03-24
**Status:** Accepted
**Decider:** Leandro Catarci (with input from Jakub Tkaczuk, Elia, Janis Tupesis WHO EMT)

## Context

The Rev-A device was powered by a Li-ion AA cell (Paleblue) boosted to 3.3 V by the TPS610981. Rev-B started from the same architecture but was reopened after a 17 March 2026 supervisor review flagged that the original decision matrix was biased toward Li-ion AA, missing the obvious third candidate — the 18650 cylindrical cell from Fionn Smith's Rev-A-precursor schematic. Both Elia and Jakub used the word "bias" repeatedly; the matrix had defended a conclusion rather than searching for one. The decision was reopened, an unbiased comparison was produced, and external clinical input was sought from Dr. Janis Tupesis (WHO EMT, deployment experience in Liberia, Haiti, Gaza) on field power realities.

The decision is mechanical (which cell + which boost converter) and a target metric of multi-week continuous battery life. The TPS610981 has near-identical regulation behaviour on AA and AAA, so cell **size** was decided separately (see [`battery-cell-size.md`](battery-cell-size.md)).

The decision-making process — supervisor pushback, Tupesis consultation, the solar feasibility investigation, and the personal reflection — is recorded separately in [`power-architecture-process.md`](power-architecture-process.md).

## Decision

Rev-B is powered by a **single rechargeable Li-ion AA cell (Paleblue) boosted to 3.3 V by the TPS610981**, with no on-PCB charging circuit (the AA cell is charged externally through its own USB-C port).

## Alternatives considered

- **18650 cylindrical cell (Smith schematic heritage).** Strongest on raw energy: 2.5–4.6× more usable capacity, $1.60–$4.55 cheaper per unit at 1000-unit scale, available in 10+/14 African countries vs 1/14 for rechargeable Li-ion AA, lower self-discharge, supports charge-while-operate via BQ25185 power path. Rejected for Rev-B because (a) a sealed internal cell with PCB-mounted charging puts wall-power transients onto the device electronics — Tupesis confirmed field power quality is dangerous (rolling blackouts, generator restarts, 220–240 V variation within a single building); (b) when the sealed cell fails after 1–2 years, the device gets discarded ("for a device this small — would get tossed in the garbage" — Tupesis); (c) higher PCB complexity (~25–30 power-section passives vs ~5 for AA), unvalidated Smith schematic, no Rev-A heritage; (d) heavier (47 g vs 19 g battery, ~90–105 g vs ~65–75 g total device — clip-on stability concern).
- **LiPo pouch cell.** Dropped by mutual agreement during supervisor review.
- **LiPo + TP4056 + LDO.** Identified as the right V3 candidate (couples naturally with the solar harvesting path) but premature for Rev-B without the V3 enclosure rework.
- **Integrated PCB-mounted solar harvesting (BQ25504 / AEM10941).** Investigated in depth (see process doc §5). Rejected for Rev-B on two grounds: (1) **structural incompatibility with AA architecture** — the AA's internal buck regulator is unidirectional, blocking reverse current from a PCB-mounted solar cell to the AA's internal Li-ion cell; (2) **thermal safety** — a device in direct equatorial sun reaches 60–80 °C interior, above the 45 °C Li-ion charging ceiling, triggering IEC 60601-1 "reasonably foreseeable misuse" testing burden. Solar remains a genuine V3 feature coupled to a LiPo + harvester architecture.
- **Hybrid (LiPo + alkaline AA OR-ing).** The strawman from the original decision matrix; not actually a viable design.

## Consequences

- **Surge resilience.** No charging circuit on the device PCB. Wall power touches the AA cell's own internal circuitry — not the medical device. This is the single biggest Tupesis-anchored argument for the AA architecture.
- **Field repairability.** Dead cell = swap a cell. The device is never bricked by a battery failure.
- **Alkaline AA fallback.** When the rechargeable cell is dead and no charging is available, the user can drop an alkaline AA in and the device runs as a consumable. Boost converter regulates either chemistry identically.
- **No CE 60601-1 burden from on-PCB charging.** No NTC-gated thermal cutoff, no Li-ion charging thermal characterisation, no IEC 60601-2-24 isolation concerns from a mains-connected charge path.
- **PCB simplicity.** ~5 passives in the power section vs ~25–30 for an 18650 + BQ25185 architecture. Faster bring-up, lower BOM, less debugging surface.
- **Honest cost paid:** 2.5–4.6× less usable energy than the 18650 path. The Phase 2 power budget (LCD always on + dual-IR-LED at 0.3 % duty + STM32G071 Stop 1) of ~190 µA at 3.3 V translates to ~700 µA from the cell at realistic boost efficiency (60 % at this load) → ~1 000 h claimable runtime on a Paleblue 2400 mAh cell. That is still ~3× the DripAssist benchmark (360 h), so the AA architecture clears the competitive bar (see [`battery-cell-size.md`](battery-cell-size.md)).
- **Lower African field availability for the rechargeable cell** (1/14 countries vs 10+/14 for the 18650). Mitigated by the alkaline AA fallback path.

The deployment model that surrounds this hardware choice — multi-unit field kit, alkaline fallback batteries, external solar charging — is captured separately in [`care-package-deployment.md`](care-package-deployment.md) and is **planned, not executed** for Rev-B.

## Revisit triggers

- If Rev-C drops the AA cell in favour of a LiPo or 18650 with on-PCB charging, revisit and produce a Rev-C-targeted comparison.
- If a future deployment context constrains the device to wholly battery-less (mains-powered) operation, revisit.
- If solar harvesting becomes a hard requirement, the AA architecture is structurally incompatible and the whole power stack reopens.
- If Phase 2 power budget grows beyond ~300 µA (e.g. always-on connectivity, more LEDs), the boost efficiency regime shifts and the AA runtime headroom may no longer justify the architecture.
