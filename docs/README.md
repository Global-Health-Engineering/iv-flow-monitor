# docs/

Project documentation written for an outside reader. The intent is that
someone who clones this repo cold can rebuild the device, understand why
each design decision was made, and reproduce the validation results without
having access to the author's private notes.

Anything written for personal thinking lives elsewhere (PARA-style notes
outside the repo). Anything that should accompany the artefact lives here.

## What goes in this folder

| File | Status | Purpose |
|------|--------|---------|
| `testing-and-validation.md` | ✅ committed | Pre-registered validation protocol (EXP-0 → EXP-6). Timestamp = pre-registration evidence. |
| `enclosure-requirements.md` | ✅ committed | Hand-off spec for follow-up theses iterating on the 3D-printed casing. Numbered REQ-x.y requirements, verification mapping, out-of-scope rationale. |
| `design-requirements.md` | planned | Requirements derived from clinical interviews, humanitarian context, IEC 60601-2-24, NICE CG174. |
| `state-of-the-art.md` | planned | Photoelectric drop detection, IV drip physiology, prior-art comparison. |
| `architecture.md` | planned | Dual-beam Phase 1 / LPTIM1 Phase 2 — first-principles derivation. The novel contribution. |
| `pcb-design.md` | planned | Power architecture, COMP1 simplification, schematic walkthrough. |
| `firmware.md` | planned | State machine diagram, drop-detection pseudocode, calibration algorithm. |
| `enclosure.md` | planned | ASA print rationale, heat inserts, fit-test outcomes. |
| `results.md` | planned | Tables + plots from the analysis notebook. The repo's core written artefact. |
| `limitations.md` | planned | Honest weaknesses ranked by impact on conclusions (sample size, drop-shape model, beam-width bias, surface tension regime). |
| `recommendations.md` | planned | V3 power, regulatory pathway, clinical validation, BOM-to-CHF 50, field trial design. |
| `conclusions.md` | planned | One conclusion per research question. No new analysis. |
| `self-caught-issues.md` | planned | Issues identified independently (BF-read protocol, buzzer ARR sharing, COMP1 floating, USART doc drift, ADC sampling). |
| `external-reproducibility.md` | planned | Peer cold-clone test result + 3-line note. |
| `project-planning.md` | planned | Project plan, contingencies (camp absence), scope adjustments. |
| `decisions/` | ✅ folder | Architecture Decision Records — see `decisions/README.md`. |

## Naming convention

- Lowercase kebab-case (`limitations.md`, not `Limitations.md` or
  `limitations_doc.md`).
- One topic per file. Cross-link with relative paths
  (`../analysis/README.md`).
- Dates in filenames only when the document is genuinely point-in-time
  (e.g. `firmware-audit-2026-04-30.md`); otherwise prefer evergreen names.

## Style

- Write for a reader who doesn't share your context. Spell out acronyms
  on first use.
- Lead with the conclusion, then the reasoning. Bury the lede only in
  the Discussion sections where building suspense serves the reader.
- Embed data tables and Mermaid diagrams inline rather than pointing at
  external files when length permits.
- Each non-trivial claim links to its evidence: a CSV under `data/`,
  a notebook cell under `analysis/`, a commit hash, a datasheet under
  `hardware/datasheets/`.

## Cross-references to other folders

- Validation data and protocol → `docs/testing-and-validation.md` →
  `data/` (raw CSVs) → `analysis/` (notebook).
- Hardware design rationale → `docs/pcb-design.md` →
  `hardware/flow_monitor.kicad_sch`.
- Firmware architecture → `docs/firmware.md` →
  `firmware/STM32CubeIDE/InfusionBA2/Core/`.
- Enclosure fit and print history → `docs/enclosure.md` →
  `enclosure/`.
