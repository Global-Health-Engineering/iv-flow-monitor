# Battery Cell Size — Retain Single AA (vs AAA)

**Date:** 2026-05-03

## Context

The Rev-B power architecture uses a single Paleblue rechargeable Li-ion AA cell boosted from 1.5 V to 3.3 V by the TPS610981 (see [`power-architecture.md`](power-architecture.md)). The AA and AAA share the same voltage profile, so cell-size selection is purely mechanical (enclosure size) and capacity (runtime). The question reopened in early May with 12 days to submission: should the AA be replaced with AAA for a 4 mm smaller cross-section on the sensor arm?

## Decision

**Retain the single Li-ion AA (Paleblue).** AAA was evaluated as an enclosure size reduction, but fails the competitive battery-life benchmark and carries enclosure redesign cost with 12 days to submission.

## Phase 2 power budget

Phase 2 is the clinically relevant operating mode: MCU in Stop 1 with LPTIM1 counting drop events via COMP1. The LCD is never off — it displays the live flow rate at all times.

### 3.3 V rail load

| Component | Current | Notes |
|---|---|---|
| STM32G071 Stop 1 + LSE running | 15 µA | RM0444 typical; LSE included |
| COMP1 high-speed mode | 3 µA | As configured in `.ioc` |
| IR LED, one beam, 0.3 % duty | 60 µA | 20 mA × 0.003; BOT beam only in Phase 2 |
| SSD1803A LCD static display | 100 µA | Controller always on; no refresh needed |
| Miscellaneous (GPIO leakage, etc.) | 10 µA | |
| **Total at 3.3 V** | **~190 µA** | |

### Battery-side current (1.5 V cell)

The STM32G071 runs at 3.3 V from the boost output, not directly from the cell. The TPS610981 at very light loads (~190 µA output) operates far below its peak efficiency. At 85 % efficiency (datasheet headline) the converter is loaded at ~1 mA; at 190 µA output the realistic efficiency is ~55–65 %. Using 60 %:

```
Output power:  3.3 V × 190 µA = 627 µW
Input power:   627 µW / 0.60  = 1,045 µW
Cell current:  1,045 µW / 1.5 V ≈ 700 µA
```

**Conservative design number: 1 mA** (includes temperature variation, actual-vs-spec efficiency, unknown board leakage).

## Claimable runtime

Claimable = calculated runtime at 1 mA, using 80 % usable cell capacity, with an additional 50 % safety margin applied to the final figure.

| Cell | Rated capacity | Usable (×0.8) | Runtime at 1 mA | Claimable (÷2) |
|---|---|---|---|---|
| AA Paleblue | 2400 mAh | 1920 mAh | 1920 h | **~1 000 h (~6 weeks)** |
| AAA Paleblue | ~800 mAh | 640 mAh | 640 h | **~300 h (~12 days)** |
| DripAssist 1.0 (AA alkaline) | — | — | — | **360 h** (manufacturer claim) |

## Why AAA fails the competitive benchmark

The closest commercial reference is DripAssist (Shift Labs), spec sheet 735-00009 Rev D: **360 h continuous on one AA alkaline** (FAQ confirms ~290 h at 24 h/day).

- **AAA Dripito claimable: ~300 h** vs **DripAssist: 360 h.** With any honest safety margin, AAA cannot support the claim "longer battery life than DripAssist."
- **AA Dripito claimable: ~1 000 h** vs **DripAssist: 360 h.** This is ~3× the benchmark — defensible and publication-worthy.

Switching to AAA removes a concrete, quantified competitive advantage in exchange for a 4 mm enclosure diameter reduction.

## Alternatives considered

- **AAA Paleblue Li-ion (smaller form factor, ~1/3 capacity).** Rejected on benchmark grounds above. Also weaker on field availability (AAA is less universally stocked than AA in LMIC contexts per Tupesis consultation, see [`power-architecture-process.md`](power-architecture-process.md) §3) and requires an enclosure redesign with 12 days to submission.

## Consequences

- **The "~3× DripAssist battery life" headline survives** as a defensible publication-grade claim.
- **Field availability advantage retained.** AA is more universally stocked than AAA in normal LMIC settings, and alkaline AA is a viable fallback in the Dripito Care Package model.
- **No enclosure redesign needed.** The Onshape model from 2026-04-23 around AA geometry remains valid; battery-holder recess and dependent features are unchanged.
- **No electrical change.** TPS610981 regulates AA and AAA identically; no power-architecture impact.

## Revisit triggers

- If clinical-usability feedback identifies enclosure size as a deployment blocker, AAA remains technically open — it requires only a mechanical redesign with no power-architecture impact.
- If a Rev-C power architecture (e.g. 18650, LiPo) is adopted, this decision is naturally superseded.
- If a cell chemistry with a non-flat discharge curve enters the architecture, the runtime calculation reopens.
