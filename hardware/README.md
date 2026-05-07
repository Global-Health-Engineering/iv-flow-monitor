# hardware/

KiCad 8.x electronic design files for the Dripito monitor PCB —
schematic, board layout, project-local symbol and footprint libraries,
component datasheets, and fabrication outputs.

## Top-level files

| File | Purpose |
|------|---------|
| `flow_monitor.kicad_pro` | KiCad project file |
| `flow_monitor.kicad_sch` | Schematic |
| `flow_monitor.kicad_pcb` | Board layout |
| `flow_monitor.kicad_prl` | Per-user layout state (committed for convenience) |
| `sym-lib-table` | Registers `lib/IV_Flow_Monitor_Symbols.kicad_sym` |
| `fp-lib-table` | Registers `IV_Flow_Monitor_Footprints.pretty/` |
| `power_analysis.md` | Power-architecture analysis notes |

## Subdirectories

| Folder | Purpose |
|--------|---------|
| [`lib/`](lib/) | Project-local KiCad symbol libraries |
| [`IV_Flow_Monitor_Footprints.pretty/`](IV_Flow_Monitor_Footprints.pretty/) | Project-local KiCad footprint library |
| [`datasheets/`](datasheets/) | Component datasheets (PDFs) for everything on the BOM |
| [`gerbers/`](gerbers/) | Gerber + drill + pick-and-place fabrication outputs |
| [`3dmodels/`](3dmodels/) | 3D models (component STPs + assembled-board STEP exports) |
| [`scripts/`](scripts/) | Hardware-side automation (logo-to-footprint converter) |

## Gitignored paths

`flow_monitor-backups/` (KiCad timed snapshots), `temp/` (KiCad
scratch), `_autosave-*`, `fp-info-cache`.

## Workflow

- Open and build only via the **KiCad GUI** — no CLI build is configured.
- Hand-edits to `.kicad_sch` / `.kicad_pcb` (e.g. via scripts): always
  reopen in the KiCad GUI before committing — these files are sensitive
  to structural regressions that pass a text diff.
- New / copied symbols must have the project name in their `instances`
  block, or KiCad refuses to load them. Don't use `extends` inheritance
  across hierarchical `lib_symbols` blocks — flatten unit definitions.

## Licensing

- Three custom footprints are CC BY-SA 4.0 (see
  [`../LICENSE-CC-BY-SA-4.0.md`](../LICENSE-CC-BY-SA-4.0.md)):
  `SW_HYP_1TS005F-2500-5001`,
  `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal`,
  `X_SW_Slide_SPDT_SSK12D07VG5`.
- All other hardware design files are CERN OHL 2.0 Permissive (see
  [`../LICENSE-CERN-OHL-2-PERMISSIVE.md`](../LICENSE-CERN-OHL-2-PERMISSIVE.md)).
