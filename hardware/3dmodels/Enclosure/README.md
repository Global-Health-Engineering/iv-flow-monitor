# hardware/3dmodels/Enclosure/

Rev-B enclosure exports from the Onshape `Dripito Rev-B` assembly.
Eight parts × two formats: STEP (parametric source, in `STEP/`) and STL
(printer-ready meshes, in `STL/`).

> The current Rev-B enclosure is **not the final mechanical design** —
> see [`../../../enclosure/README.md`](../../../enclosure/README.md) and
> [`../../../docs/decisions/chamber-holder-mechanism.md`](../../../docs/decisions/chamber-holder-mechanism.md).
> A full mechanical rework is expected for Rev-C.

## Layout

```
Enclosure/
├── STEP/   # Parametric solid models (CAD-tool ingestion, dimensional reference)
└── STL/    # Triangulated meshes (slicer ingestion, FDM printing)
```

Both folders contain the same eight parts under matching filenames — `Front_Case.step` ↔ `Front_Case.stl`, etc. The STEPs are the authoritative geometry source from Onshape; the STLs are derived for slicer ingestion.

## Parts

### Printable enclosure pieces (six)

| File | What it is |
|------|------------|
| `Front_Case` | Front-plate housing — LCD window, button cutouts, LED bezel holes |
| `Back_Casing` | Rear shell of the device body |
| `body` | Main body shell that carries the PCB |
| `Gear` | Sliding-gear chamber holder with the IR-beam pass-through hole (see [`../../../docs/decisions/chamber-holder-mechanism.md`](../../../docs/decisions/chamber-holder-mechanism.md)) |
| `lock` | Gear retention / closure piece |
| `pins` | Alignment / fastener pins between mating halves |

All six print in ASA white per [`../../../docs/decisions/enclosure-material.md`](../../../docs/decisions/enclosure-material.md). Print profile defaults: 0.2 mm layer (sensor-arm optical faces at 0.15 mm), 4-perimeter walls, 30 % gyroid infill, tree supports where required.

### Component reference models (two, not printable)

| File | What it is |
|------|------------|
| `AA_Battery` | AA Li-ion cell — present in the assembly for clearance / fit checks |
| `slide_switch` | SK-12D07-G slide switch — the off-board mode/power switch reference model |

## Source

Onshape document `Dripito Rev-B`. The exporter is manual — regenerate both formats from Onshape after meaningful CAD changes and overwrite the corresponding files in `STEP/` and `STL/`. Keep STEP and STL in sync.

## Printing

For a one-shot Rev-B prototype, feed the six printable STLs into a slicer (PrusaSlicer / OrcaSlicer / Bambu Studio) configured for ASA per the print profile defaults above. The two component STLs (`AA_Battery`, `slide_switch`) are not printed.
