# docs/decisions/ — Architecture Decision Records

One file per significant architectural or engineering decision. The point
is that a reader can reconstruct *why* the design looks the way it does
without asking the author. Each decision page is a contract with the
future: what was decided, what alternatives were rejected, what would
trigger a revisit.

## File format

Each decision is a single Markdown file with a stable structure:

```markdown
# <Decision title>

**Date:** YYYY-MM-DD
**Status:** proposed | accepted | superseded by [link] | reverted
**Decider:** Leandro Catarci (with input from <list>)

## Context
What problem does this solve? What constraints apply? What did we know
that the reader doesn't?

## Decision
The chosen option, stated unambiguously. One sentence if possible.

## Alternatives considered
Each alternative + why it lost. Cost, risk, complexity, supplier
availability — be concrete.

## Consequences
What this decision unlocks. What it forecloses. What we now have to live
with that we didn't before.

## Revisit triggers
Conditions under which this decision should be re-opened (e.g.
"if Rev-C uses a Li-ion cell, revisit boost converter selection").
```

## Naming convention

- Lowercase kebab-case, action-or-noun phrase: `comparator-simplification.md`,
  `power-architecture.md`, `auto-calibration-at-boot.md`.
- No dates in filename (the date is inside the file, in the frontmatter
  block above). Files are evergreen even after they're superseded.
- A superseded decision **stays in the repo** with `Status: superseded by
  [link]`. Deleting it loses the reasoning trail.

## Planned decision records

These are decisions already made during the Rev-B work and tracked in the
author's private notes. They will be imported into this folder before
submission:

| File | Topic |
|------|-------|
| `comparator-simplification.md` | COMP1 → comparator-only simplification |
| `optical-architecture.md` | Dual-beam Phase 1 / LPTIM Phase 2 trade-off |
| `power-architecture.md` | TPS610982 boost converter selection |
| `enclosure-material.md` | ASA white, M2 brass heat inserts, 0.2 mm layer |
| `enclosure-geometry.md` | Sensor arm + front plate geometry |
| `sensor-arm-alignment.md` | Direct FDM vs steel dowel pin (deferred) |
| `chamber-holder-mechanism.md` | Drip chamber retention mechanism |
| `usb-interface-removal.md` | USB-C dropped from Rev-B |
| `back-casing-extrude.md` | Back casing extrusion choice |
| `battery-cell-size.md` | AA Li-ion vs alternatives |
| `battery-indicator.md` | Battery state-of-charge indicator scheme |
| `led-duty-cycle.md` | IR LED PWM duty cycle |
| `auto-calibration-at-boot.md` | Optional auto-cal vs manual `#define` thresholds |
| `onshape-mcp-evaluation.md` | CAD tooling decision |

This folder will fill in over the Week-4 polish sprint (2026-05-11 →
2026-05-13) per the project plan in `../project-planning.md`.

## Why ADRs

A code review or supervisor reading the repo cold cannot see the
discussions, dead ends, and stakeholder pushback that shaped the design.
The ADR format makes that history explicit and durable. It captures
tacit engineering judgement as documented rationale a future
contributor or reviewer can audit.

Reference: Michael Nygard, "Documenting Architecture Decisions" (2011),
the canonical ADR pattern.
