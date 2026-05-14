# hardware/3dmodels/Enclosure/

Rev-B enclosure exports from the Onshape `Dripito Rev-B` assembly. The folder splits into the
printable subset (`STL/`) and the full parametric source (`STEP/`).

> The current Rev-B enclosure is **not the final mechanical design** —
> see [`../../../enclosure/README.md`](../../../enclosure/README.md) and
> [`../../../docs/decisions/chamber-holder-mechanism.md`](../../../docs/decisions/chamber-holder-mechanism.md).
> A full mechanical rework is expected for Rev-C.

## Layout

```
Enclosure/
├── STEP/   # Full Onshape assembly — 3 printable parts + 5 component reference models
└── STL/    # Rev-B printable subset — 3 parts only (slicer-ready meshes)
```

The STEPs are the authoritative geometry source from Onshape and include the full assembly
(printable parts plus reference geometry for off-the-shelf components used for clearance and
fit checks). The STLs in `STL/` are the printable subset actually fed into the slicer for the
Rev-B build.

## Printable parts (in `STL/` and `STEP/`)

| File | What it is |
|------|------------|
| `Front_Case` | Front-plate housing — LCD window, button cutouts, LED bezel holes |
| `Back_Casing` | Rear shell of the device body |
| `Gear` | Sliding-gear chamber holder with the IR-beam pass-through hole (see [`../../../docs/decisions/chamber-holder-mechanism.md`](../../../docs/decisions/chamber-holder-mechanism.md)) |

All three print in ASA white per [`../../../docs/decisions/enclosure-material.md`](../../../docs/decisions/enclosure-material.md). Print profile defaults: 0.2 mm layer (sensor-arm optical faces at 0.15 mm), 4-perimeter walls, 30 % gyroid infill, tree supports where required.

## Component reference models (in `STEP/` only — not printed)

| File | What it is |
|------|------------|
| `AA_Battery` | AA Li-ion cell — clearance / fit reference |
| `body`, `lock`, `pins` | FFC connector sub-bodies (housing, actuator, contact pins) — clearance reference for the on-PCB FFC connector |
| `slide_switch` | SK-12D07-G slide switch — off-board mode/power switch reference |

These remain in `STEP/` for assembly-level fit-checks. They are deliberately omitted from
`STL/` because they are off-the-shelf components, not printable.

## Source

Onshape document `Dripito Rev-B`. The exporter is manual — regenerate STEPs from Onshape after
meaningful CAD changes; export only the printable subset to `STL/`.

## Printing

For a one-shot Rev-B prototype, feed the three STLs in `STL/` (`Front_Case`, `Back_Casing`,
`Gear`) into a slicer (PrusaSlicer / OrcaSlicer / Bambu Studio) configured for ASA per the
print profile defaults above.
