# Power Architecture — Decision Process Record

**Date:** 2026-03-26 (process records 2026-03-17 → 2026-03-26)
**Status:** Companion to [`power-architecture.md`](power-architecture.md) (Accepted)
**Decider:** Leandro Catarci

> This is a record of *how* the power architecture decision was made — the supervisor pushback, the external clinical consultation, the solar feasibility investigation, and the methodology used to produce an unbiased comparison. The decision itself (Li-ion AA + TPS610981 boost) lives in [`power-architecture.md`](power-architecture.md).

## 1. Timeline

**17 March 2026** — Submitted a formal Energy Architecture Decision Matrix to supervisors Jakub Tkaczuk and Elia. The document compared three options: Li-ion AA (Option A), LiPo pouch cell (Option B), and a LiPo + alkaline AA hybrid with automatic power-path OR-ing (Option C). The matrix used 7 weighted criteria, a sensitivity analysis with tornado perturbation and 4 deployment scenarios, a 3-year TCO model, and a simplified FMEA. It recommended Option A — the rechargeable Li-ion AA with alkaline fallback.

**~20 March** — Received critical feedback from both Elia and Jakub. The core message from both reviewers was that the analysis was biased toward a pre-determined conclusion (Option A), disproportionate in depth relative to the decision, and missing the most obvious alternative (18650 cylindrical cell). Jakub noted that Option C (the hybrid) was an implausible strawman, and that the 18650 from Fionn Smith's V2 schematic was the natural third candidate. Elia flagged that the input data was skewed across multiple criteria and that the cost comparison used inconsistent sourcing.

**~21 March** — Responded to supervisors acknowledging the bias and proposing to consult Dr. Janis Tupesis for an independent clinical perspective. Jakub approved the approach and simultaneously shared his own AI-assisted power analysis covering 17 metrics across Li-ion AA, LiPo pouch, and 18650, sourced from LCSC, manufacturer datasheets, and a 14-country African availability survey. Its summary favoured the 18650 as the "strongest overall" option.

**23 March** — Received Tupesis's field feedback. He addressed three questions about AA availability, charging access, and device end-of-life in humanitarian contexts.

**24 March** — Produced an updated, unbiased comparison document incorporating data from both analyses plus Tupesis's new evidence. Investigated solar trickle charging feasibility.

**26 March** — Decision committed to Li-ion AA + Care Package deployment model.

## 2. Supervisor Feedback — What It Actually Said

The feedback was not primarily about AI usage or analysis depth. Both reviewers used the word "bias" repeatedly. The substantive criticisms were:

**Elia's key points:** The five-model sensitivity analysis was overkill for a straightforward question. The input data was heavily biased — Continuity of Care scores treated battery management as trivial for the 30-day-runtime options; Environmental Resilience ignored that Option A also uses lithium chemistry constrained by the same temperature limits; the cost comparison mixed Alibaba and Bastelgarage pricing inconsistently; the BOM was incomplete; and Option B was actually cheaper than stated when sourced consistently from Alibaba/LCSC.

**Jakub's key points:** The report read as a justification, not a comparison. Option C (hybrid) was a strawman — the obvious third option was the 18650 from Fionn's design. The Continuity of Care score of 5/5 for AA vs 3/5 for LiPo was asymmetric: the charging infrastructure dependency applies equally to both (the USB-C port is just on the battery vs on the device). The shipping section should score equal unless IATA certification is being pursued. The sensitivity analysis was opaque and unnecessary for answering the actual design question. No sources were cited for component numbers.

## 3. Tupesis Field Feedback — New Evidence

Dr. Janis Tupesis (emergency physician, WHO EMT Initiative, deployment experience in Liberia, Haiti, and other humanitarian contexts) provided three key data points that neither analysis had addressed.

**Field power quality is dangerous.** Voltage varies 220–240 V within a single building (measured by power company in Liberia). No surge protection exists at most facilities. Rolling blackouts and generator restarts cause large transients. Equipment damage from surges is common — Tupesis has seen phones, ultrasounds, and CT scanners destroyed. This is not an edge case; it is routine.

**Small devices with dead internal batteries get discarded.** When asked what happens to a sealed device whose battery fails after 1–2 years, Tupesis said: *"for a device this small — would get tossed in the garbage."* Some hospitals have maintenance staff who attempt improvised repairs, but this is unpredictable and not something to design around.

**AA batteries are ubiquitous in normal LMIC settings but scarce in true emergencies.** Tupesis confirmed that AAs are available "pretty ubiquitously at kiosk, small stores, etc." in normal low-to-middle income settings, but noted that in acute humanitarian emergencies (e.g. Gaza) all batteries become harder to source. All batteries are import products everywhere in Africa.

**Tupesis also suggested integrating a small solar panel** on the back of the device for trickle charging — inspired by the concept of solar-backed pagers. This triggered the feasibility investigation in §5.

## 4. Updated Comparison — Summary of Trade-Offs

A full comparison was produced covering 14 metrics with consistent LCSC pricing for ICs and Alibaba/manufacturer pricing for batteries at 1000-unit scale. The LiPo pouch was dropped by mutual agreement. Only Li-ion AA (removable, Rev-A heritage) and 18650 (sealed internal, Smith schematic heritage) were compared.

**Where the 18650 is stronger.** 2.5–4.6× more usable energy and runtime. $1.60–$4.55 cheaper per unit. Available in 10+/14 African countries vs 1/14 for rechargeable Li-ion AA. Best self-discharge (1–3 %/month vs 5–8 %/month — AA penalised by internal buck regulator quiescent draw). Best hot-climate resilience. Supports charge-while-operate via BQ25185 power path.

**Where the Li-ion AA is stronger.** Surge resilience — no charging circuit on the PCB means wall power never touches device electronics (Tupesis evidence). Field repairability — dead battery = swap a cell, dead sealed device = trash (Tupesis evidence). Weight — 19 g vs 47 g battery, ~65–75 g vs ~90–105 g total device, matters for clip-on stability. PCB simplicity — ~5 vs ~25–30 power-section passives, proven Rev-A circuit vs unvalidated Smith schematic. Alkaline fallback — device never fully bricks, degrades to consumable operation. No enclosure redesign needed. Zero DG burden for shipping spare alkaline batteries.

**Context-dependent factors.** Continuity of care depends on whether the site has reliable USB power (favours 18650) or not (favours AA fallback). Operator familiarity is a wash — both interaction models are intuitive but with different failure modes.

**Open questions requiring physical data.** Clip stability at 95–105 g (weighted mockup test). HT7733A as TPS610981 cost-saving replacement. Quality of unbranded Alibaba Li-ion AA cells. Smith schematic validation on breadboard.

## 5. Solar Trickle Charging — Feasibility Assessment

Investigated whether Tupesis's suggestion of an on-device solar panel could be implemented.

**Power budget analysis.** The maximum panel area that could fit on the device (~100 × 40 mm = 40 cm²) would generate roughly 800 mW peak outdoors in direct Sub-Saharan African sun. However, Dripito operates indoors at a patient's bedside. At hospital lighting levels (300–500 lux), the same panel produces approximately 1–2 mW accounting for angle losses and spectral mismatch. This is 20–40 % of best-case power draw and under 3 % of worst-case. Not enough to sustain the device, but enough to meaningfully slow battery drain and offset self-discharge during storage.

**Architectural incompatibility with AA.** Solar harvesting requires an onboard rechargeable cell that the harvesting IC (e.g. TI BQ25504) can charge directly. Li-ion AA batteries have an internal buck converter between the cell and the output terminals — this is one-directional and cannot accept reverse current. The only charging path is through the AA's own USB-C port, which expects 5 V USB input. There is no electrical path from a PCB-mounted solar cell to the internal cell of a removable Li-ion AA. **Solar harvesting is therefore structurally incompatible with the AA architecture.** It requires an onboard LiPo or 18650 with direct cell terminals accessible to the harvesting IC.

**Thermal safety concern.** A device left in direct tropical sun could reach internal temperatures of 60–80 °C. Li-ion cells have a 45 °C charging ceiling — charging above this accelerates degradation and risks thermal runaway. Solving this requires NTC-gated charging cutoff, thermal characterisation, and potentially IEC 60601-1 "reasonably foreseeable misuse" testing. Solvable but not trivial.

**Validated open-source reference designs identified.**
- Pesky Products BQ25504 breakout (Hackaday.io / OSH Park) — 0.5×0.5 inch, validated with STM32L4 at ~1.8 mA perpetual operation outdoors, 2018 Hackaday Prize semifinalist.
- BQStripped (GitHub, KiCad) — minimal BQ25504 PCB, Gerbers on OSH Park.
- Teapot Labs BWLR1E (GitHub, KiCad) — complete STM32WLE + AEM10941 solar LoRa sensor node, open hardware.
- Mabon et al. (2019), Wiley open access — STM32 + solar node with 40.7 cm² panel, dimensioning methodology.

**Conclusion.** Solar is a genuine V3 feature that couples naturally with the LiPo + TP4056 + LDO architecture already identified as the V3 candidate. It cannot be bolted onto the AA architecture.

## 6. Final State

**Decision committed (2026-03-26):** Li-ion AA + the "Dripito Care Package" deployment model for Rev-B. The cell-chemistry decision is recorded in [`power-architecture.md`](power-architecture.md). The Care Package deployment surround — multi-unit field kit, alkaline AA fallback, external 5 V 2 W USB solar panel, USB-C cable — is recorded as planned-not-executed in [`care-package-deployment.md`](care-package-deployment.md).

**Solar harvesting** is parked as a Rev-C research track coupled to a LiPo + harvester architecture. The investigation in §5 above stands as the open-source reference work for whoever picks it up.
