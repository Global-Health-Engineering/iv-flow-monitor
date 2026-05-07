# hardware/gerbers/

Fabrication outputs for the Dripito Rev-B PCB: Gerber files (one per
copper / mask / silk / paste / outline layer), drill files (PTH and
NPTH), pick-and-place files, the bundled `.zip` for fab-house upload,
and the `.gbrjob` job description.

These files are **regenerated** from `../flow_monitor.kicad_pcb` — the
`.kicad_pcb` is the source of truth. Treat the Gerbers as build
artefacts that happen to be committed for traceability.

## What's here

| File | Layer / role |
|------|--------------|
| `flow_monitor-F_Cu.gtl` / `-B_Cu.gbl` | Front / back copper |
| `flow_monitor-F_Mask.gts` / `-B_Mask.gbs` | Front / back solder mask |
| `flow_monitor-F_Silkscreen.gto` / `-B_Silkscreen.gbo` | Front / back silkscreen |
| `flow_monitor-F_Paste.gtp` / `-B_Paste.gbp` | Front / back paste mask |
| `flow_monitor-Edge_Cuts.gm1` | Board outline |
| `flow_monitor-PTH.drl` / `-NPTH.drl` | Plated / non-plated drill |
| `flow_monitor-top.pos` / `-bottom.pos` | Pick-and-place coordinates |
| `flow_monitor-job.gbrjob` | Job description (Gerber X3) |
| `flow_monitor.csv` | Component-position CSV (assembly) |
| `flow_monitor_gerbers.zip` | Bundled archive for fab-house upload |
| `placement/` | Auxiliary pick-and-place outputs |

## Re-exporting

After a layout change, regenerate via KiCad → *File → Fabrication
Outputs* (Gerbers, Drill Files, Component Placement). Re-zip
`flow_monitor_gerbers.zip` from the freshly generated files. Commit
with a message that names the source PCB commit:
`refactor(hardware): regenerate gerbers after <change>`.

## Fab-house

Default target: JLCPCB. 2-layer, 1.6 mm, ENIG or HASL. The same
Gerber + drill bundle works for PCBWay; pick-and-place CSV format may
need a per-fab conversion.
