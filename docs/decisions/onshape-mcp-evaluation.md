# Onshape MCP Evaluation — Not Adopted for Rev-B

**Date:** 2026-05-01

## Context

The community Onshape MCP server (`hedless/onshape-mcp`, v0.3.0, 2026-03-02) exposes Onshape's parametric CAD API through the Model Context Protocol so that LLM-based agents can read variable tables, create sketches and features, and export model formats. The mechanical work on Dripito's enclosure (sensor arm, front plate, chamber-holder geometry, mounting bosses, LCD cutout) is parametric in nature — drip-chamber OD, sensor-arm-to-PCB standoff, LED bezel diameter, button bore size — and would in principle benefit from automated variable-table iteration if the tooling were sufficient.

## Decision

**The Onshape MCP server was evaluated for Rev-B and not adopted.** The Rev-B enclosure was completed in Onshape directly via the GUI.

## Why not adopted

The Onshape MCP exposes 45 tools covering variable-table read/write, parametric sketch and feature creation (rectangles, circles, lines, arcs, extrude, revolve, fillet, chamfer, boolean operations, linear and circular patterns), assembly mate creation, and STL/STEP/PARASOLID/GLTF/OBJ export. Sufficient on paper for the kind of variable-driven enclosure tweaks anticipated for Rev-C and beyond. Two limitations made it unsuitable for the current revision:

1. **Sketch constraints (coincident, parallel, horizontal/vertical) are not exposed.** Geometry placed via the MCP is not robustly constrained against variable changes — a downstream variable update can break the geometry rather than driving it. For parametric work this is the key feature that's missing.
2. **Sketches can only be created on the three standard planes.** Not on existing feature faces. This forecloses the mounting-boss, LCD-cutout, and arm-clamp work that dominates enclosure iteration — most real CAD work places sketches on faces of already-extruded features.

Combined with the setup cost (Onshape API credential provisioning, document-tree learning) and the Rev-B enclosure deadline already slipped to 2026-04-30, the cost/benefit was negative.

## Alternatives considered

- **Adopt the MCP now for Rev-B parametric work.** Rejected on the two functional gaps above plus the schedule cost at the wrong moment in the sprint.
- **Skip the evaluation entirely.** Rejected: knowing whether parametric agent-driven CAD is viable for Dripito's enclosure work is a Rev-C-relevant question and the evaluation itself is cheap once the tool's tools list is read.

## Consequences

- **Rev-B enclosure work was completed in the Onshape GUI by hand.** No automation overhead; no novel failure modes from agent-driven CAD.
- **The evaluation note exists for the next iteration.** A Rev-C author considering parametric CAD has a documented reading of where the upstream tool stands as of 2026-05-01.

## Revisit triggers

- If sketch-on-face support lands upstream in `hedless/onshape-mcp` (or an equivalent tool), the central blocker is removed and the cost/benefit shifts.
- If a sensitivity study across wall-thickness / material variants becomes part of the Rev-C analysis, variable-table iteration plus scripted STL export would pay back the setup cost.
- If Onshape itself ships first-party MCP / agent support with full sketch-constraint coverage, this evaluation is superseded.
