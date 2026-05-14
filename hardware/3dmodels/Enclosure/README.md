# hardware/3dmodels/Enclosure/

STEP exports of the Rev-B enclosure from the Onshape `Dripito Rev-B`
assembly. Eight parts: six 3D-printable enclosure pieces + two
component reference models that sit in the assembly for visualisation.

> The current Rev-B enclosure is **not the final mechanical design** —
> see [`../../../enclosure/README.md`](../../../enclosure/README.md) and
> [`../../../docs/decisions/chamber-holder-mechanism.md`](../../../docs/decisions/chamber-holder-mechanism.md).
> A full mechanical rework is expected for Rev-C.

## Printable enclosure parts

| File | What it is |
|------|------------|
| `Front_Case.step` | Front-plate housing — LCD window, button cutouts, LED bezel holes |
| `Back_Casing.step` | Rear shell of the device body |
| `body.step` | Main body shell that carries the PCB |
| `Gear.step` | Sliding-gear chamber holder with the IR-beam pass-through hole (see [`../../../docs/decisions/chamber-holder-mechanism.md`](../../../docs/decisions/chamber-holder-mechanism.md)) |
| `lock.step` | Gear retention / closure piece |
| `pins.step` | Alignment / fastener pins between mating halves |

All six print in ASA white per [`../../../docs/decisions/enclosure-material.md`](../../../docs/decisions/enclosure-material.md). Print profile defaults: 0.2 mm layer (sensor-arm optical faces at 0.15 mm), 4-perimeter walls, 30 % gyroid infill, tree supports where required.

## Component reference models (not printable)

| File | What it is |
|------|------------|
| `AA_Battery.step` | AA Li-ion cell — present in the assembly for clearance / fit checks |
| `slide_switch.step` | SK-12D07-G slide switch — the off-board mode/power switch reference model |

## Source

Onshape document `Dripito Rev-B`. The exporter is manual — regenerate from Onshape after meaningful CAD changes and overwrite the corresponding STEPs here. STL exports for slicer ingestion can be added as siblings (`<part>.stl`) as needed.
