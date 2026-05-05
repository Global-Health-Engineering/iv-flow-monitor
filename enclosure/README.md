# enclosure/

3D-printed mechanical housing for the Dripito monitor — sensor arm, front
plate, hinged chamber-holder lid, back shell, and any printable
accessories. Source CAD lives in Onshape; this folder holds the
**exported, version-controllable** artefacts that downstream consumers
(printer slicers, contract manufacturers, follow-up theses) need to
reproduce a unit.

> **For follow-up MSc theses iterating on the enclosure:** read
> [`../docs/enclosure-requirements.md`](../docs/enclosure-requirements.md)
> first. It is the requirements spec. This README documents the *current*
> artefact set; the spec documents *what the artefact must satisfy*.

## Layout

```
enclosure/
├── onshape_exports/             # Parasolid / STEP from the Onshape source
│   ├── dripito_rev_b_assembly.step
│   ├── sensor_arm.step
│   ├── front_plate.step
│   ├── chamber_holder_lid.step
│   └── back_shell.step
├── stl/                         # Printer-ready meshes
│   ├── sensor_arm.stl
│   ├── front_plate.stl
│   ├── chamber_holder_lid.stl
│   └── back_shell.stl
├── print_settings/              # Slicer profiles + per-part overrides
│   ├── prusaslicer_asa_dripito.ini
│   ├── orcaslicer_asa_dripito.json
│   └── per_part_overrides.md    # "sensor arm: 0.15 mm layer at optical face" etc.
└── print_history/               # Iteration log — what printed, what failed, why
    ├── 2026-05-04_pla_dry_run.md
    ├── 2026-05-07_asa_first.md
    └── ...
```

## Source of truth

- The Onshape document `Dripito Rev-B` is the canonical CAD source. Edits
  happen there.
- After every meaningful CAD change, regenerate the STEPs and STLs in this
  folder. The exporter is manual — there is no automation yet.
- `print_history/` is append-only, one file per print attempt. Includes:
  filament spool, slicer profile commit hash, ambient temp, observed
  defects, fix applied next iteration. This is a notebook, not just a log
  — future-you and successor theses depend on it.

## Material

ASA white (Acrylonitrile Styrene Acrylate). Decision rationale lives in
`../docs/decisions/enclosure-material.md` (forthcoming). Brief: chosen
over PETG (lower UV resistance) and ABS (higher warping risk) for outdoor
humanitarian deployment contexts.

Hardware fasteners: M2 brass heat-set inserts. M2 button-head screws.

## Print profile defaults

- Layer height: 0.2 mm (sensor arm: 0.15 mm at optical faces)
- Wall count: 4
- Top/bottom layers: 5
- Infill: 30 % gyroid
- Print orientation: see `per_part_overrides.md` — sensor arm prints with
  the optical bore axis vertical so the LED/PD bores form circular cross
  sections rather than stair-stepped ellipses
- Support: tree, only where required (mostly the chamber-holder lid hinge)
- Heat-set inserts: install with a soldering iron at 240 °C, M2 brass

Calibrate the printer for ASA before running the parts (enclosed
chamber, 100 °C bed, 250 °C nozzle nominally — varies by spool).

## Compatibility (drip chamber size)

Designed for ISO 8536-4-compliant drip chambers, **14–24 mm outer
diameter** (microdrip + standard adult macrodrip). Validated against a
Ø20 mm reference chamber. Wide-body / transfusion chambers (25–30 mm)
are **out of scope** for Rev-B — addressable in a future revision via
an interchangeable cradle insert reusing the same optical-bay
interface. See [`../docs/enclosure-requirements.md`](../docs/enclosure-requirements.md)
for the full spec.

## Known issues in current Rev-B print (as of 2026-05-04)

The first ASA enclosure printed 2026-05-04 has known geometric
imperfections that were accepted to unblock validation:

- (To be enumerated in `print_history/2026-05-04_pla_dry_run.md` and
  reflected in `../docs/limitations.md` once the validation campaign is
  complete.)

These are tracked, not hidden. A successor working on Rev-C should treat
the May-04 print as a known-imperfect baseline rather than the target
geometry.

## Cross-references

- Requirements spec for Rev-C / follow-up:
  [`../docs/enclosure-requirements.md`](../docs/enclosure-requirements.md)
- Material decision:
  [`../docs/decisions/enclosure-material.md`](decisions/enclosure-material.md)
  (forthcoming)
- Chamber holder mechanism decision:
  `../docs/decisions/chamber-holder-mechanism.md` (forthcoming)
- Sensor arm geometry decision:
  `../docs/decisions/sensor-arm-alignment.md` (forthcoming)
- Geometry measurement protocol (EXP-1):
  [`../docs/testing-and-validation.md`](../docs/testing-and-validation.md)
- Geometry data per board:
  [`../data/geometry.json`](../data/README.md)
