# hardware/lib/

Project-local KiCad **symbol** libraries. Footprints live separately in
`../IV_Flow_Monitor_Footprints.pretty/`.

## Contents

| File | What it is |
|------|------------|
| `IV_Flow_Monitor_Symbols.kicad_sym` | Custom symbols specific to this project |
| `PTS647SN38SMTR2_LFS.kicad_sym` | Symbol for the PTS647SN38SMTR2 LFS tactile switch |

## Registration

These libraries are registered to the project via `../sym-lib-table` at
the parent `hardware/` level. Opening the project loads them
automatically — no per-machine library setup required.

## Adding a symbol

1. Create or copy the symbol into `IV_Flow_Monitor_Symbols.kicad_sym`
   via the KiCad Symbol Editor.
2. Ensure the symbol's `instances` block carries the project name
   (`flow_monitor`) — KiCad refuses to load symbols missing this on
   re-open, and the failure mode is silent reference de-linking on the
   schematic.
3. Inner `lib_symbols` unit names must **not** carry the library prefix
   (a recurring KiCad gotcha).
4. Avoid `extends` inheritance across hierarchical `lib_symbols`
   blocks — flatten unit definitions instead.

## What does not belong here

- KiCad standard-library symbols. Use them by reference; don't copy them
  into the project library.
- Footprints (those go to `../IV_Flow_Monitor_Footprints.pretty/`).
- 3D models (those go to `../3dmodels/`).
