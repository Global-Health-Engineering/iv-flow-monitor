# hardware/3dmodels/

3D models for component visualisation in the KiCad PCB editor and the
exported board `.step`. Footprints in `../IV_Flow_Monitor_Footprints.pretty/`
reference these models.

## Contents

| File | What it is |
|------|------------|
| `PTS647SN38SMTR2_LFS.stp` | 3D model for the PTS647 tactile switch |
| `flow_monitor.step` | Assembled-board STEP export from KiCad (board only) |
| `flow_monitor_full.step` | Assembled-board STEP export including 3D component models |
| `Neuer Ordner/` | Stray third-party folder, gitignored — not part of this project |

## Conventions

- One file per component, named after the part's MPN: `<MPN>.stp` or
  `<MPN>.wrl`.
- STEP (`.stp` / `.step`) is preferred over VRML (`.wrl`) — STEP
  preserves geometry for the assembled board export.
- Files come from manufacturer or distributor websites
  (DigiKey / Mouser / vendor "3D model" download links). Do not commit
  models without a clear provenance — note the source in the matching
  decision record or the BOM entry.

## License caveat

Manufacturer 3D models often carry redistribution restrictions. Most
explicitly permit inclusion in derivative PCB designs and assembled
mechanical models, but not standalone redistribution. If you are
publishing this repo separately, audit each `.stp` against its source
license terms. For models with unclear licensing, replace them with a
generic shape or omit and accept the cosmetic loss in the `.step`
export.

## Linking from a footprint

In the KiCad Footprint Editor:

1. *Properties → 3D Models → Add*.
2. Use a relative path: `${KIPRJMOD}/3dmodels/<MPN>.stp` so the link
   travels with the project.
3. Save the footprint. The board's `.step` export now picks up the
   model automatically.
