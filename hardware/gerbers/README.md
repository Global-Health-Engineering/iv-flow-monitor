# hardware/gerbers/

Fabrication outputs for the Dripito Rev-B PCB: Gerber files (one per
copper / mask / silk / paste / outline layer), drill files (PTH and
NPTH), pick-and-place files, the bundled `.zip` for fab-house upload,
and the `.gbrjob` job description.

These files are **regenerated** from `../flow_monitor.kicad_pcb` — the
KiCad `.kicad_pcb` is the source of truth. Treat the Gerbers as build
artefacts that happen to be committed for traceability.

## What's here

| File | Layer |
|------|-------|
| `flow_monitor-F_Cu.gtl` | Front copper |
| `flow_monitor-B_Cu.gbl` | Back copper |
| `flow_monitor-F_Mask.gts` | Front solder mask |
| `flow_monitor-B_Mask.gbs` | Back solder mask |
| `flow_monitor-F_Silkscreen.gto` | Front silkscreen |
| `flow_monitor-B_Silkscreen.gbo` | Back silkscreen |
| `flow_monitor-F_Paste.gtp` | Front paste mask |
| `flow_monitor-B_Paste.gbp` | Back paste mask |
| `flow_monitor-Edge_Cuts.gm1` | Board outline |
| `flow_monitor-PTH.drl` | Plated through-hole drill |
| `flow_monitor-NPTH.drl` | Non-plated through-hole drill |
| `flow_monitor-top.pos` | Top pick-and-place coordinates |
| `flow_monitor-bottom.pos` | Bottom pick-and-place coordinates |
| `flow_monitor-job.gbrjob` | Job description (Gerber X3) |
| `flow_monitor.csv` | Component-position CSV (assembly) |
| `flow_monitor_gerbers.zip` | Bundled archive for fab-house upload |
| `placement/` | Auxiliary pick-and-place outputs |

## Re-exporting

To regenerate after a layout change:

1. In KiCad → *File → Fabrication Outputs → Gerbers* with the standard
   layer set above. Output to `hardware/gerbers/`.
2. *File → Fabrication Outputs → Drill Files* (PTH + NPTH).
3. *File → Fabrication Outputs → Component Placement* (top + bottom).
4. Re-zip `flow_monitor_gerbers.zip` from the freshly generated files.
5. Commit with a message that names the source schematic / PCB commit
   the Gerbers were generated from (`refactor(hardware): regenerate
   gerbers after <change>`).

## Fab-house notes

- Default target fab: JLCPCB (see `jlcpcb` skill for design rules and
  ordering workflow). 2-layer, 1.6 mm, ENIG or HASL.
- For PCBA orders, the pick-and-place CSV in `flow_monitor.csv` is the
  one to upload alongside a JLCPCB-format BOM (see the `bom` skill for
  the format conversion).
- For PCBWay or alternate fabs, the same Gerber + drill bundle works;
  pick-and-place CSV format may need conversion (see `pcbway` skill).
