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

## Decision records in this folder

| File | Topic |
|------|-------|
| [`comparator-simplification.md`](comparator-simplification.md) | COMP1 → internal-comparator simplification (remove LMV331) |
| [`optical-architecture.md`](optical-architecture.md) | Dual-beam Phase 1 / LPTIM Phase 2 trade-off |
| [`power-architecture.md`](power-architecture.md) | Single Li-ion AA via TPS610981 boost |
| [`power-architecture-process.md`](power-architecture-process.md) | Companion record: how the power decision was made (supervisor pushback, Tupesis consultation, solar feasibility) |
| [`enclosure-material.md`](enclosure-material.md) | ASA white, FDM, snap-fit |
| [`enclosure-geometry.md`](enclosure-geometry.md) | External AA holder on sensor arm as counterbalance |
| [`sensor-arm-alignment.md`](sensor-arm-alignment.md) | FDM in Rev-B; injection moulding pathway for Rev-C |
| [`chamber-holder-mechanism.md`](chamber-holder-mechanism.md) | Sliding gear with IR-beam pass-through (Rev-C rework expected) |
| [`usb-interface-removal.md`](usb-interface-removal.md) | USB-C dropped; 5-pin UART debug header instead |
| [`battery-cell-size.md`](battery-cell-size.md) | AA retained vs AAA (DripAssist battery-life benchmark) |
| [`care-package-deployment.md`](care-package-deployment.md) | Planned deployment kit (3–5 units + alkaline AA fallback + external USB solar panel); not executed in Rev-B |
| [`battery-indicator.md`](battery-indicator.md) | Low-battery symbol via threshold (deferred to Rev-C) |
| [`led-duty-cycle.md`](led-duty-cycle.md) | Phase 2 IR LED at 0.3 % duty cycle |
| [`auto-calibration-at-boot.md`](auto-calibration-at-boot.md) | Threshold auto-calibration (primary, no fallback) |
| [`onshape-mcp-evaluation.md`](onshape-mcp-evaluation.md) | Parametric CAD tooling — evaluated, deferred to Rev-C |
| [`firmware-build-and-test-rev-c.md`](firmware-build-and-test-rev-c.md) | CubeIDE-only Rev-B firmware build; Dockerized build + host-side state-machine tests deferred to Rev-C |

## Why ADRs

A code review or supervisor reading the repo cold cannot see the
discussions, dead ends, and stakeholder pushback that shaped the design.
The ADR format makes that history explicit and durable. It captures
tacit engineering judgement as documented rationale a future
contributor or reviewer can audit.

Reference: Michael Nygard, "Documenting Architecture Decisions" (2011),
the canonical ADR pattern.
