# hardware/3dmodels/

3D models for component visualisation in the KiCad PCB editor, the
exported board `.step`, and the mechanical enclosure exports. Organised
into subfolders by what each model represents.

## Layout

```
hardware/3dmodels/
├── PCB/              # Board + on-PCB component models
│   ├── PTS647SN38SMTR2_LFS.stp
│   ├── flow_monitor.step
│   └── flow_monitor_full.step
└── Enclosure/        # Mechanical enclosure exports from Onshape (STEP + STL)
                      # (populated as the source CAD is exported)
```

## PCB models

| File | What it is |
|------|------------|
| `PCB/PTS647SN38SMTR2_LFS.stp` | 3D model for the PTS647 tactile switch |
| `PCB/flow_monitor.step` | Assembled-board STEP export from KiCad (board only) |
| `PCB/flow_monitor_full.step` | Assembled-board STEP export including 3D component models |

Conventions for PCB models:

- One file per component, named after the part's MPN: `<MPN>.stp` or `<MPN>.wrl`.
- STEP (`.stp` / `.step`) preferred over VRML (`.wrl`) — STEP preserves geometry for the assembled board export.
- Models come from manufacturer or distributor websites (DigiKey / Mouser / vendor 3D-model download links). Note provenance in the BOM entry.

## Enclosure models

Source CAD lives in Onshape (`Dripito Rev-B`). STEP and STL exports land in `Enclosure/` for version-controlled distribution to slicers and downstream consumers.

The current Rev-B enclosure is **not the final mechanical design**. It exists to integrate the PCB + chamber holder + optics + battery into a testable assembly so the rest of the device can be validated. A full rework is expected for Rev-C — see [`../../docs/decisions/chamber-holder-mechanism.md`](../../docs/decisions/chamber-holder-mechanism.md), [`../../docs/decisions/sensor-arm-alignment.md`](../../docs/decisions/sensor-arm-alignment.md), and [`../../docs/decisions/enclosure-material.md`](../../docs/decisions/enclosure-material.md) for the rationale and Rev-C path.

## Stray folders

`Neuer Ordner/` is a third-party download artefact, gitignored — not part of this project.

## License caveat

Manufacturer 3D models often carry redistribution restrictions. Most explicitly permit inclusion in derivative PCB designs and assembled mechanical models, but not standalone redistribution. If you are republishing this repo separately, audit each `.stp` against its source license terms. For models with unclear licensing, replace them with a generic shape or omit and accept the cosmetic loss in the `.step` export.

## Linking from a footprint

In the KiCad Footprint Editor:

1. *Properties → 3D Models → Add*.
2. Use a relative path: `${KIPRJMOD}/3dmodels/PCB/<MPN>.stp` so the link travels with the project.
3. Save the footprint. The board's `.step` export now picks up the model automatically.
