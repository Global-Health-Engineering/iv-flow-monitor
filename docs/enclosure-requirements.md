# Enclosure Requirements — Dripito Monitor

Specification for the 3D-printed mechanical housing. Written as a hand-off
document for a follow-up MSc/BSc thesis or a Rev-C revision: this file
defines *what the enclosure must do*; the artefacts in
[`../enclosure/`](../enclosure/) are *how the current revision satisfies
those requirements*.

A successor revising the enclosure should not have to re-derive these
requirements from clinical interviews and catalogues — that work was done
once for Rev-B and is captured here. Update this file when adding,
removing, or reframing a requirement; do not silently invalidate it.

## How to read this document

- **shall** — mandatory. A revision that fails a `shall` is a regression.
- **should** — strongly recommended. Deviating requires written
  justification in the revision's design notes.
- **may** — optional / informational.
- Each requirement carries an ID (`REQ-x.y`). Future revisions can cite
  IDs in their commit messages and decision records to make
  satisfies/breaks traceable.

## Scope

The enclosure houses one Dripito monitor PCB plus its battery, LCD,
buttons, status LEDs, optical front-end (IR emitters and photodiodes),
and a holder for a clinical IV drip chamber. It is intended for use in
humanitarian healthcare settings — low-resource clinics, paediatric
wards, field deployments. The current revision is FDM-printed; downstream
revisions may be injection-moulded but the requirements below remain
material-agnostic where possible.

**Out of scope:** sterilisation requirements (the device contacts the IV
chamber externally only; no fluid path goes through the enclosure),
implantable-grade biocompatibility, IP67 immersion ratings, lifecycle >
2 years of continuous outdoor exposure.

---

## 1. Material requirements

- **REQ-1.1** The enclosure **shall** be printable from ASA
  (Acrylonitrile Styrene Acrylate). Rationale: superior UV resistance
  vs. PETG, lower warping vs. ABS, accepted humanitarian-deployment
  durability profile. See `decisions/enclosure-material.md`
  (forthcoming).
- **REQ-1.2** The enclosure **should** be printable in white filament.
  Rationale: lower solar heat absorption in high-ambient-temperature
  field settings; better visibility of dirt to prompt cleaning.
- **REQ-1.3** The geometry **shall not** require materials with thermal
  performance beyond ASA's working envelope (continuous use up to
  ~85 °C). A revision that requires a more demanding material must
  justify the substitution against the deployment-temperature use case.
- **REQ-1.4** The enclosure **may** be substituted with PA12 / nylon for
  injection-moulded production runs at higher unit volumes, provided
  REQ-1.1's UV-resistance equivalent is preserved.

## 2. Geometric / mechanical requirements

- **REQ-2.1** All electronic components on the Dripito Rev-B PCB
  (`../hardware/flow_monitor.kicad_pcb`) **shall** fit within the
  enclosure with ≥ 1 mm clearance between any component top surface and
  the enclosure interior wall.
- **REQ-2.2** PCB-to-enclosure mounting **shall** use M2 brass
  heat-set inserts. Threaded plastic posts are not acceptable
  (insufficient thread durability for repeated assembly during
  servicing).
- **REQ-2.3** Threaded fasteners **shall** be M2 button-head screws of
  length appropriate to the boss depth. Non-captive screws are
  acceptable.
- **REQ-2.4** The enclosure **shall** allow PCB removal and
  re-installation without destructive disassembly.
- **REQ-2.5** Snap-fit features **may** be used for non-load-bearing
  closures (e.g. the back shell) provided the snap features do not need
  to be defeated to access the PCB for service.
- **REQ-2.6** Wall thickness **shall** be ≥ 2.0 mm at any
  unsupported region; ≥ 1.5 mm where backed by a rib or boss.
- **REQ-2.7** The enclosure outer dimensions **should not** exceed
  150 mm × 100 mm × 60 mm. Hand-portability and shelf-fit in clinical
  trolleys constrain the upper bound.

## 3. Optical-path requirements

These requirements derive from the dual-beam drop-detection architecture
(see `architecture.md`, forthcoming). They are the most failure-sensitive
requirements: violating any of REQ-3.x produces silently bad data.

- **REQ-3.1** The drip chamber, when seated in the holder, **shall** sit
  in a fixed, repeatable position relative to the sensor arm. The
  chamber **shall** be referenced (datumed) against the rigid
  sensor-arm side of the holder, not centred between two compliant
  faces. Rationale: optical path length must remain constant
  irrespective of chamber outer diameter.
- **REQ-3.2** The sensor arm **shall** present two horizontal infrared
  optical paths through the drip chamber, separated vertically by a
  nominal `d` of 14.0 mm (CAD nominal). This separation is the basis of
  the dual-beam velocity model (see EXP-1 in `testing-and-validation.md`).
- **REQ-3.3** The board-to-board standard deviation of measured beam
  separation across an assembled batch **shall** be ≤ 1.0 mm. Higher
  variance is a print-tolerance issue and must be addressed before the
  affected boards are used for validation. (See EXP-1 verification
  procedure.)
- **REQ-3.4** The IR emitter and photodiode optical apertures **shall**
  align with the chamber drop column to within ±0.5 mm in both the
  horizontal and vertical axes when the chamber is seated.
- **REQ-3.5** Stray ambient light reaching the photodiode at any sun /
  room-lamp incidence **should** be attenuated such that the baseline
  ADC value drift over 60 s is < 5 % of the signal dip during a drop
  passage. (Quantitatively verified in EXP-5 EC-03.)
- **REQ-3.6** The optical bore in the sensor arm (housing the LED and
  PD) **shall** be printed with its axis vertical (parallel to the
  chamber drop column) so the bore wall forms a circular cross-section
  rather than a stair-stepped ellipse. This is a print-orientation
  requirement, not a CAD requirement, and must be carried into the
  per-part slicer settings.
- **REQ-3.7** Replacing or recalibrating the LED / PD pair **shall** be
  possible without disturbing the sensor-arm-to-chamber datum
  (REQ-3.1). Practically: the optics module should be a sub-assembly
  that can be removed and reinstalled within the same alignment
  tolerance.

## 4. Drip-chamber compatibility

- **REQ-4.1** The chamber holder **shall** accept ISO 8536-4-compliant
  drip chambers with outer diameter in the range **14–24 mm**. This
  range covers microdrip / paediatric (14–17 mm) and standard adult
  macrodrip (18–22 mm) classes plus a manufacturing tolerance buffer
  (22–24 mm). Source: `../docs/decisions/chamber-holder-mechanism.md`
  (forthcoming) → drip-chamber diameter survey.
- **REQ-4.2** Wide-body / transfusion chambers (25–30 mm OD) are
  **explicitly out of scope** for the Rev-B baseline. A future revision
  **may** support them via an interchangeable cradle insert reusing the
  same optical-bay interface (REQ-3.7).
- **REQ-4.3** The holder **shall** retain a chamber against accidental
  bumping at any orientation within ±15° of vertical. Falling out
  during use is unacceptable.
- **REQ-4.4** The holder **shall** allow chamber installation and
  removal one-handed by a clinician. Two-handed operation is a fail.
- **REQ-4.5** Chamber installation **should** be possible without
  disconnecting the IV line above or below the chamber.

## 5. Holder mechanism

- **REQ-5.1** The holder **shall** use a vertical-axis hinged-clamshell
  topology: a fixed body carrying the sensor arm, optics, and PCB; a
  hinged passive lid that captures the chamber against the fixed side.
  Rationale and prior art: `../docs/decisions/chamber-holder-mechanism.md`
  (forthcoming).
- **REQ-5.2** The hinge axis **shall not** carry electrical signals.
  No FFC, no wires across the hinge.
- **REQ-5.3** The lid **shall** include a compliant gripper face (e.g.
  silicone / TPE pads, or printed compliant flexure) sized to span the
  REQ-4.1 OD range without changing the chamber's referenced position
  on the fixed side (REQ-3.1).
- **REQ-5.4** The hinge axis **shall** be located on whichever lateral
  side of the holder does **not** carry the optical-bezel datum, so
  opening the lid never disturbs alignment.
- **REQ-5.5** Closure **may** be friction-only, magnetic, or a printed
  snap. Whichever is chosen, it must require positive intent to open
  (i.e. cannot self-open under gravity or vibration in normal use).

## 6. User-interface integration

- **REQ-6.1** The enclosure **shall** present an LCD viewing window
  sized for the DOGS164W-A 4×16 character LCD with a minimum 1 mm
  bezel margin around the active area.
- **REQ-6.2** Tactile-button cutouts **shall** be provided for all
  buttons present on the active firmware revision. For Rev-B (firmware
  `InfusionBA2`) this is MUTE / MODE / RES (3 buttons). The cutout
  locations match the Rev-B PCB silk; future revisions update CAD as
  the PCB changes.
- **REQ-6.3** Buttons **shall** be operable with one finger by an adult
  clinician wearing nitrile examination gloves.
- **REQ-6.4** Status LED bezels (battery / mode indicators) **shall**
  be visible in indoor-fluorescent ambient lighting from a viewing
  distance of 1 m.
- **REQ-6.5** The buzzer aperture **shall not** attenuate the alarm
  tone by more than 6 dB(A) at 1 m relative to the un-enclosed PCB
  measurement.
- **REQ-6.6** A power switch / battery compartment **shall** be
  accessible without removing the PCB.

## 7. Power / battery integration

- **REQ-7.1** The enclosure **shall** house the AA-cell battery solution
  used by Rev-B (single AA Li-ion routed via FFC, see
  `../docs/decisions/battery-cell-size.md`, forthcoming).
- **REQ-7.2** Battery insertion / removal **shall** be possible without
  tools.
- **REQ-7.3** A future Rev-C may switch to an 18650 Li-ion cell. The
  enclosure **may** anticipate this by leaving room or providing an
  alternate battery-bay STL, but must not require the change.

## 8. Environmental / deployment requirements

- **REQ-8.1** The enclosure **shall** be wipe-cleanable with isopropyl
  alcohol (IPA, ≤ 70 %) and standard medical disinfectant wipes
  without crazing or visible degradation in routine clinical use.
- **REQ-8.2** The enclosure **should** target IP54 ingress protection
  as a design goal. IP54 is the design target, **not** a tested
  specification — Rev-B is **not** validated to IP54 and any claim of
  IP54 compliance must wait on quantitative testing.
- **REQ-8.3** The enclosure **shall** survive a 1 m drop onto vinyl
  flooring without functional damage. Cosmetic damage is acceptable.
- **REQ-8.4** Operating temperature range: 5 °C to 45 °C ambient.
  Storage: −10 °C to +60 °C.
- **REQ-8.5** The enclosure **should** carry no sharp edges or pinch
  points exposed to a clinician's hands during normal use or chamber
  installation.

## 9. Manufacturability requirements

- **REQ-9.1** All printed parts **shall** print on a hobbyist-class
  FDM printer with a build volume of 220 × 220 × 250 mm or larger
  (Prusa i3, Bambu A1, equivalent).
- **REQ-9.2** No part **shall** require dissolvable / soluble support
  material. Standard tree / break-away supports only.
- **REQ-9.3** The print **should** complete each part in ≤ 8 hours on
  the reference printer at the documented profile, to support iterative
  development cycles.
- **REQ-9.4** Each printable part **shall** ship with a documented
  print profile in `../enclosure/print_settings/` (slicer ini/json
  plus per-part overrides).
- **REQ-9.5** Heat-set insert installation **shall** be documented:
  insert geometry, soldering iron tip, temperature, depth.
- **REQ-9.6** The full set of parts for one device **should** require
  ≤ 200 g of ASA filament.

## 10. Verification

How each requirement category is verified:

| Category | Verification | Where evidence lives |
|----------|--------------|----------------------|
| Material (REQ-1.x) | Print + visual inspection + IPA wipe test | `enclosure/print_history/` |
| Mechanical fit (REQ-2.x) | Test PCB inserted, screws torqued, snap features cycled 5× | `enclosure/print_history/` |
| Optical alignment (REQ-3.x) | EXP-1 caliper measurement of `d` per board; EXP-0 detection-gate test | `data/geometry.json`, `data/calibration_log.csv` |
| Chamber fit (REQ-4.x) | Physical fit test with 14, 18, 20, 22, 24 mm chambers (or shimmed phantoms) | `enclosure/print_history/` + `docs/limitations.md` |
| Holder mechanism (REQ-5.x) | One-handed install / remove demo, ±15° tilt retention test | `enclosure/print_history/` |
| User interface (REQ-6.x) | Gloved-hand button test, LCD-readability check at 1 m | `enclosure/print_history/` |
| Environmental (REQ-8.x) | IPA wipe, drop test from 1 m, ambient temp survey | `enclosure/print_history/` |
| Manufacturability (REQ-9.x) | Reference profile print on Prusa MK4 / Bambu A1; mass measurement | `enclosure/print_settings/` + `print_history/` |

## 11. Known gaps in the current Rev-B implementation

(To be filled in once the validation campaign 2026-05-07 → 2026-05-10
identifies which requirements the May-04 print fails. Each gap is then
either fixed in a Rev-B re-print, or accepted-with-rationale and entered
into `../docs/limitations.md`.)

## 12. Out of scope (and why)

- **Sterilisation cycles (autoclave, EtO, gamma).** The device contacts
  the chamber externally only; the IV fluid path is closed. Surface
  cleaning (REQ-8.1) is sufficient.
- **IP67 immersion.** Field-clinic deployment does not require
  immersion resistance. IP54 design target (REQ-8.2) is the maximum
  ingress claim.
- **Wide-body / transfusion chambers (25–30 mm OD).** Excluded from
  REQ-4.1 to keep the holder simple. A future revision may revisit.
- **Integration with peristaltic pumping.** Dripito monitors gravity
  infusion only.
- **Continuous outdoor exposure > 2 years.** ASA's UV resistance is
  good but not infinite; the device is intended for indoor /
  shaded clinical use with occasional transport.
- **Conformity assessment for medical-device certification (CE, FDA).**
  Out of scope for Rev-B as a research artefact; flagged in
  `../docs/recommendations.md` (forthcoming) as a Rev-C / commercial
  requirement.

## Cross-references

- Validation procedure (incl. EXP-1 geometry):
  [`testing-and-validation.md`](testing-and-validation.md)
- Decision records (forthcoming):
  - `decisions/enclosure-material.md`
  - `decisions/chamber-holder-mechanism.md`
  - `decisions/sensor-arm-alignment.md`
  - `decisions/back-casing-extrude.md`
  - `decisions/battery-cell-size.md`
- Current artefact set: [`../enclosure/`](../enclosure/)
- Drip-chamber diameter survey (basis for REQ-4.1): summarised in
  `decisions/chamber-holder-mechanism.md` (forthcoming).
