# Limitations

Scope of the Rev-B validation campaign and the constraints under which the numbers in `docs/results.md` should be interpreted. Items are ordered by impact on the conclusions.

## 1. Drop-shape oscillation is the fundamental residual error

The chord-time architecture measures the **vertical extent** of each drop at the beam plane, then assumes a sphere to compute volume. Drops in free fall oscillate between oblate (squashed vertically) and prolate (elongated vertically) for the first 10–30 mm after detaching from the chamber tip — the device's beam plane catches each drop at an unpredictable point in this oscillation. Over many drops the bias averages out (hence `V_CAL_K = 1.27` works on the run mean), but the per-drop CV stays inflated, and the per-run k spans 0.87–1.40 across V_50_01..04 even after the mean-pulse algorithm absorbs the optical-channel asymmetry.

Consequence: post-`V_CAL_K` per-run residual is ±30 %. A Rev-C optical front-end with two horizontally-separated beam pairs (catching horizontal as well as vertical extent of each drop) would let the firmware infer the oscillation phase and apply an oscillation-aware volume formula. Out of scope for Rev-B.

## 2. Two-orifice divergence (invalidates per-drop matching)

The device measures drops at the **drip-chamber orifice** (where they form). The scale captures mass at the **end-of-tubing orifice** (where they fall out into the catch vessel). These two orifices have different geometry and different surface-tension dynamics, so they drip at different rates with different drop sizes. Mass conservation gives:

```
N_chamber × V_chamber = N_end × V_end = total mass passed through
```

but **N_chamber ≠ N_end** and chamber drops cannot be matched 1:1 to scale steps. The 2026-05-13 campaign saw end-orifice drop counts 1.5–2× the chamber-drop counts. The valid ground truth at this granularity is therefore the per-run chamber-drop average `V_true_chamber = mass / N_UART`, not a per-drop pairing. `tools/match_scale_drops.py` is preserved as an exploratory diagnostic only; its docstring documents this invalidation.

## 3. TOP-vs-BOT optical asymmetry (backsplash + intrinsic)

The TOP and BOT photodiodes report systematically different pulse widths for the same drop crossing both beams (BOT/TOP pulse ratio 1.75–2.50× at the original device position with `CAL_MARGIN_HIGH=100`; physics-expected ratio 0.92×).

The 2026-05-13 backsplash falsifiability test (~16:00) repositioned the device higher on the drip chamber so the BOT beam was further from the pool surface: the BOT/TOP ratio fell to ~1.13×. Lowering `CAL_MARGIN_HIGH` to 30 at the same higher position made the ratio jump to ~7.8× as the lower threshold caught a long BOT splash tail invisible at margin=100. Interpretation: the BOT photodiode sees a real splash-driven extension that the margin=100 threshold clips, but a small intrinsic asymmetry persists even at the higher position.

The firmware mean-of-pulses approach partially absorbs this (BOT over, TOP under → mean roughly tracks truth) and `V_CAL_K = 1.27` absorbs the residual. A Rev-C optical front-end with the BOT beam moved further from the pool, plus TOP/BOT gain equalisation, would close the gap.

## 4. Tilt sensitivity (qualitative, un-quantified)

The bench observed that small device-attitude changes break drop detection: a sub-mm reposition of the chamber doubled the TOP pulse width (1.5 ms → 3.1 ms) and brought drops back into the detection envelope. The mechanism is that off-vertical drop trajectories cause the lateral position at the BOT beam to diverge from the TOP-beam crossing point, and once the offset exceeds the beam width the TOP→BOT sequence never closes. Magnitude of the tolerance was not measured. Captured in `D:\Obsidian\Dripito\01 Projects\Dripito Monitor\Logs\Bench Findings 2026-05-13.md`; the chamber-holder mechanism is to be revisited with a verticality budget for Rev-C.

## 5. `V_CAL_K = 1.27` is fitted to the same runs it is validated against

The scalar correction `V_CAL_K` is the unweighted mean of per-run `k_pre` across V_50_01..04. Reporting per-run residual against these four runs is therefore a *self-consistency* check, not an independent validation. V_50_05 (run after baking `V_CAL_K` into firmware) is the independent verification; its `k_post` is the first generalisation check. Multi-day / multi-board / multi-fluid generalisation is out of scope for Rev-B.

## 6. V_50_04 has a 248 s mid-run UART gap

V_50_04 is included in the 4-run calibration set because it bounds the slow end of the operating envelope, but its UART stream contains a 248 s gap of unknown cause (mix of real drip pauses and threshold-miss events not separable from this run alone). Its `V_true_chamber = 186.10 µL` is therefore an **upper bound** on the actual chamber-drop volume, and its `k_pre = 1.13` contributes one of four equal votes to `V_CAL_K`. Treating V_50_04 as upper-bound rather than excluding it was a judgment call — `V_CAL_K` shifts to 1.31 without it.

## 7. Tethered 3.3 V supply

The validation dataset is collected with 3.3 V supplied directly to the MCU VDD via the ST-Link debugger, bypassing the TPS610982 boost converter from the single-cell battery design. The dataset validates the optical detection chain, sphere-model calibration, and dual-beam time-of-flight architecture. The field power chain (1 × AA Li-ion → boost → MCU) is deferred to Rev-C.

## 8. n = 1 board for geometry

The beam separation in `data/geometry.json` (`mean = 10.2 mm, sd = 0.3 mm`) reflects caliper repeats on a single board; board-to-board scatter from the printed sensor arm is un-quantified. Manufacturing-tolerance impact on `d` is documented by the a priori MC error budget but not verified across multiple physical boards.

## 9. Drop-to-infusion volume coupling

The device measures drop volume at the chamber; the volume the patient receives is downstream of the chamber. Tubing compliance, air bubbles, capillarity, and pressure dynamics decouple the two. The bench gravimetric is also upstream of the catheter, so this decoupling is invisible to the validation. Named here as a scope limitation rather than a bias term. See `D:\Obsidian\Dripito\01 Projects\Dripito Monitor\Notes\Drop-to-Infusion Volume Coupling.md` for the longer treatment.

## 10. Single drip set; wide observed drop-volume range

The validation uses a single drip set labelled macro 20 gtt/mL (nominal 50 µL/drop). Bench gravimetric across V_50_01..04 saw `V_true_chamber` range from 39.26 µL to 186.10 µL — a 4.7× spread within the same drip set, fluid, and board. This appears to be a **flow-rate-dependent** effect (slowest clamp → largest drops; fastest in-envelope clamp → smallest drops), consistent with surface-tension dominance at low flow and drag-driven early detachment at high flow. The spread means a fixed nominal-V_set approach (e.g., "always 50 µL") would be wrong by up to 4× at the operating-envelope extremes.

## 11. Improvised chamber holder

The fixture is bench-grade, not clinical-grade. Positional uncertainty estimated at ±2 mm — material for the residual TOP/BOT asymmetry and the tilt-sensitivity finding. A ringstand-grade or printed-clamp fixture is the post-Rev-B mechanical revision.

## 12. No Rev-A baseline

The earlier InfusionBA firmware on STM32G030C8TX was removed in commit `ed84ff5` of this repository. Recovering a Rev-A baseline (count-only, fixed-factor) for direct comparison was not feasible within the project timeline. The literature baseline for fixed-factor methods is cited in `analysis/notebooks/error_budget.ipynb`.

## 13. Head height fixed

A single head height (drip chamber to TOP beam) was used in the validation. Clinical scenarios span 60–150 cm — drop velocity and orifice dynamics change across that range. Out of scope for Rev-B.

## 14. Bench-day firmware constants modified during the campaign

The firmware constants in effect during the 2026-05-13 bench were not the as-committed values at the start of the day. Changes applied in-bench and committed in the same PR:
- `BEAM_WIDTH_MM`: 5.0 → 0.0 (W=5 over-corrected, causing 100 % DROP_REJECT)
- `CAL_MARGIN_HIGH`: 220 → 100 → 30 (transiently for the backsplash test) → 100 (final)
- `CAL_MARGIN_LOW`: 80 → 30 → 10 (transient) → 30 (final)
- `D_MM_MIN`: 1.0 → 0.1
- `V_CAL_K`: new constant 1.27 introduced after V_50_01..04 calibration

Each is documented in the firmware comments with a 2026-05-13 dated note explaining the bench observation that motivated the change.

## 15. Single bench day

The full validation campaign is one bench session (2026-05-13). Run-to-run scatter across sessions (drip-set settling, optical-alignment drift, ambient-IR variation) is un-quantified.

## 16. Print-tolerance dominance is predicted but not refuted

The a priori MC error budget attributes 49 % of the predicted MAPE to per-board printed-sensor-arm geometry scatter. Bench was run on a single board, so this prediction is consistent with the data but not independently verified.

## 17. Position-dependence — `V_CAL_K` does not generalise across mount heights

A second bench session on the afternoon of 2026-05-13 mounted the device at three different heights on the same drip chamber (same drip set, same fluid, same board) and measured the K required to make the LCD-summed drop volume match the gravimetric reading. The required K varied from 0.28 to 1.27 across positions — not the ±30 % per-run residual quoted from the V_50_01..05 morning campaign, but a 4.5× range driven by mount geometry alone. Raw runs live in `data/raw/2026-05-13_pm_position_drift/` with a per-run README.

Three position-dependent contaminants of the chord measurement were isolated:

1. **Umbilical at TOP** (mounts close to the drip orifice). The drop has not fully separated from the chamber tip when it crosses the TOP beam; the fluid filament extends the TOP pulse trailing edge. Observed `pulse_TOP_low` was 6200–7300 µs at low mounts vs 2200 µs at the V_50_05-era high mount, for physically near-identical drops.
2. **Backsplash at BOT** (mounts close to the chamber pool). Splash particles propagate up through the BOT beam after the drop body has cleared it, extending the BOT pulse trailing edge. `pulse_BOT_low / pulse_TOP_low` ratio was 2.3 at the V_50_05-era position vs 0.92 (gravity-expected) at intermediate mounts.
3. **Threshold-vs-peak mismatch** at the dual-threshold (CAL_MARGIN_CORE=150) core pulse. The same drop's peak ADC reaches a roughly constant absolute level (3870–3920 on BOT, 4000–4015 on TOP at this board's saturation behaviour), but the boot-cal baseline varies per session by 100–200 counts. A fixed-margin core threshold therefore cuts at a different fraction of (peak − baseline) per boot, changing the pulse duration by ~10 % and the cubed volume estimate by ~30 %.

Several algorithm variants were trialled — TOP-low only, BOT-low only, BOT-core only, TOP-core only, mean-of-pulses, leading-half-pulse (entry-to-peak timing), hybrid with BOT/TOP ratio splash detection, and an adaptive EMA core threshold that updated thresh_core toward `baseline + 0.5×(peak − baseline)` after each drop. The best cross-position result across the 11 afternoon runs was a hybrid (BOT_core in normal regimes, TOP_low when BOT/TOP > 1.5 signalled splash) giving residuals of +1.4 % at one position, −22 % at another, and −34 % at a third. **No single (algorithm, K) combination passed ±5 % at all positions.**

Architectural conclusion: with Rev-B optics — one TOP photodiode whose dynamic range above baseline depends on the drop-to-beam geometry, and one BOT photodiode close enough to the chamber pool to see splash at high mounts — the optical chord-time architecture **does not deliver a single position-invariant `V_CAL_K`**. The two beams *do* deliver position-agnostic velocity (transit time) and reliable drop counting at most positions; what they don't deliver is a position-invariant chord measurement, because every chord-time threshold inherits one or both of the umbilical/splash contaminants depending on mount height.

The Rev-C path is named in §1 and §3: a second pair of horizontally-separated beams catching the drop's horizontal extent (to remove the sphere-from-vertical-chord ambiguity that drop oscillation creates), wider TOP-to-BOT separation so drops have fully detached before either beam, and TOP/BOT gain equalisation so the dynamic-range issue at TOP disappears. The Rev-B firmware was reverted to the committed `V_CAL_K = 1.27` mean-pulse state at the end of the 2026-05-13 pm session; the position-dependence finding is documented here without changing the V_50 headline in `docs/results.md`.
