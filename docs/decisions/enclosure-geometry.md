# Enclosure Geometry — External AA Holder on Sensor Arm for Counterbalance

**Date:** 2026-03-15
**Status:** Accepted
**Decider:** Leandro Catarci

## Context

The Rev-B device clips onto an IV pole via the chamber holder ([`chamber-holder-mechanism.md`](chamber-holder-mechanism.md)) and carries the PCB + battery + LCD + buttons on a sensor arm. The AA cell is the heaviest single mass in the device (~25 g). Where it sits on the assembly affects the sensor arm's gravitational moment about its IV-pole mounting point and therefore the risk of the device rotating under its own weight during use.

## Decision

The AA battery holder is positioned **externally on the sensor arm, on the opposite side of the IV-pole clamp from the chamber**. This serves a dual function: power source and mechanical counterbalance. The ~25 g cell offsets the moment that the chamber + holder + electronics impose on the clamp.

## Alternatives considered

- **Internal battery compartment (Rev-A style).** Cell sits inside the main body, contributing to the moment on the chamber side rather than counterbalancing it. Better packaging aesthetics, worse mechanics.
- **Separate counterweight mass (no electrical function).** Could decouple the counterbalance design from cell placement, but adds part count + weight without delivering any other function. Rejected on principle.

## Consequences

- **Reduced device rotation under its own weight on the clamp.** Better static mechanical stability for the clip-on form factor.
- **Increased horizontal footprint.** The external holder protrudes from the assembly, which may interfere with adjacent IV lines or equipment in a crowded clinical bay. This is a real cost of the counterbalance choice; not yet quantified against real clinical-bay geometry.
- **Battery is user-accessible without opening the device.** Cell swap is a single hand operation. Aligns with the field-repairability argument in [`power-architecture.md`](power-architecture.md).
- **The counterbalance effect depends on clamp friction and exact mass distribution.** The geometry was derived from the Onshape model and has not yet been validated with a weighted physical prototype on a real IV pole.

## Revisit triggers

- If the device proves to interfere with adjacent IV lines or equipment in clinical use, the external-holder horizontal footprint reopens — internal compartment becomes the natural fallback, with explicit counterweight if needed.
- If a Rev-C cell-chemistry change (e.g. 18650, LiPo) shifts the dominant mass, the counterbalance math redoes itself.
- If the IV-pole-clamp mechanism changes (different clamp friction, different mounting geometry), the moment calculation reopens.
