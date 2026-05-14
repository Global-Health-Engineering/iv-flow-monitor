# LED Duty Cycle — Phase 2 IR LED at 0.3 %

**Date:** 2026-04-01

## Context

The [Phase 2 single-beam continuous-monitoring mode](optical-architecture.md) drives the IR LED at a low duty cycle to fit the multi-week runtime budget on a single Li-ion AA (see [`power-architecture.md`](power-architecture.md), [`battery-cell-size.md`](battery-cell-size.md)). The Phase 2 duty cycle is bounded above by the slowest drop's shadow duration (must catch every drop) and below by the analog front-end's settling time (must allow the photodiode bias chain + comparator to reach steady state before sampling). Earlier notes referenced 0.1 % as a design target; this ADR fixes the actual achievable value at 0.3 %.

## Decision

**Phase 2 LED duty cycle = 0.3 %** (5 µs ON / 1.8 ms period). Period locked at ≤ 1.8 ms; minimum pulse width fixed at ~5 µs.

```
TON    = 5    µs   (LED on-time per pulse)
TOFF   = 1795 µs   (LED off-time)
Period = 1800 µs   (1.8 ms, matches Rev-A timing baseline)
Duty   = 0.28 %    (≈ 0.3 %)
```

LPTIM1 clocked from LSE (32.768 kHz) generates the 1.8 ms period. TIM1_CH2 PWM on PB3 controls the 5 µs pulse width.

## Hard constraints

### Period (≤ 1.8 ms)

Guaranteed detection requires at least one LED pulse during every drop's shadow.

| Drip set | gtt/mL | Min shadow duration | Max safe period (–14 % margin) |
|----------|--------|---------------------|--------------------------------|
| Adult | 20 | 3.60 ms | ~3.0 ms |
| Micro | 60 | 2.50 ms | ~2.1 ms |
| Neonatal | 100 | 2.10 ms | ~1.8 ms |

Period is locked to ≤ 1.8 ms to catch neonatal drops.

### Minimum pulse width (TON ≥ ~5 µs)

The analog front-end settling chain sets the floor.

| Stage | Time |
|-------|------|
| Photodiode bias RC settling (R14 × C8 = 330 ns, 5τ) | ~1.6 µs |
| COMP1 blanking (avoid turn-on transient false trigger) | ~3 µs |
| COMP1 propagation (medium speed) | ~0.2 µs |
| Detection margin | ~1 µs |
| **Total minimum TON** | **~5 µs** |

### Resulting duty cycle

```
duty = TON_min / T_period_max = 5 µs / 1800 µs ≈ 0.28 %
```

Rounded to **0.3 %** for margin.

## Alternatives considered

- **0.1 % duty cycle (previous design target).** With the 1.8 ms period locked by neonatal-set detection, 0.1 % would require TON = 1.8 µs — below the analog settling floor. Rejected.
- **Faster analog front-end (TIA op-amp instead of resistor load).** Would reduce the settling floor and allow lower duty, but adds an op-amp and breaks the BOM simplicity goal of the comparator-simplified architecture (see [`comparator-simplification.md`](comparator-simplification.md)). Not worth the trade.
- **Restrict drip-set support to adult sets only.** Allows period = 5 ms, TON = 5 µs → 0.1 % duty achievable. Lost on scope: Rev-B explicitly supports micro / neonatal drip sets.
- **Probabilistic detection (catch ~40 % of drops, correct statistically).** Unacceptable for a medical device; rejected on principle.

## Consequences

- **Average IR LED current ≈ 57 µA** (from 19 mA peak × 0.3 %). The 0.3 % → 0.1 % gap saves 38 µA on average — less than the STM32G071 Stop-mode current of ~5–15 µA. Diminishing returns; 0.3 % already captures the meaningful win vs Rev-A's 8.3 % planned duty (96.4 % reduction).
- **The 5 µs TON is right at the analog settling floor.** Any change to the photodiode bias network (R14, C8) or COMP1 blanking value forces a re-derivation of the minimum pulse width and potentially a new duty target.
- **The 1.8 ms period locks Phase 2 to the neonatal-drip-set support claim.** Dropping neonatal scope would relax the period and allow lower duty; adding faster drip sets (paediatric microdrip extremes) might force shorter periods.

## Revisit triggers

- If the analog front-end is redesigned (different photodiode, different bias network, op-amp added), the minimum TON re-derives and this ADR reopens.
- If drip-set scope changes (drop neonatal, add finer micro), the period bound shifts and the duty cycle reopens.
- If a deeper Stop mode becomes available on the MCU that reduces the always-on current floor, the relative gain from going below 0.3 % grows and the trade-off shifts.
