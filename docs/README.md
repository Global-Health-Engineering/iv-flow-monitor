# docs/

Project documentation written for an outside reader. The intent is that
someone who clones this repo cold can rebuild the device, understand why
each design decision was made, and reproduce the validation results
without having access to the author's private notes.

Anything written for personal thinking lives elsewhere (PARA-style notes
outside the repo). Anything that should accompany the artefact lives here.

## Documents in this folder

| File | Purpose |
|------|---------|
| [`testing-and-validation.md`](testing-and-validation.md) | Pre-registered validation protocol (EXP-0 → EXP-6). Timestamp = pre-registration evidence. |
| [`results.md`](results.md) | Bench-day results: per-run V_true vs V_LCD, V_CAL_K derivation, residuals. |
| [`limitations.md`](limitations.md) | Honest weaknesses ranked by impact on conclusions; includes §17 position-dependence finding. |
| [`enclosure-requirements.md`](enclosure-requirements.md) | Hand-off spec for follow-up theses iterating on the 3D-printed casing. Numbered REQ-x.y requirements, verification mapping, out-of-scope rationale. |
| [`decisions/`](decisions/) | Architecture Decision Records — see [`decisions/README.md`](decisions/README.md). |
| [`bench/`](bench/) | Bench-day session notes and finding logs. |

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

- Validation data and protocol → [`testing-and-validation.md`](testing-and-validation.md) →
  [`../data/`](../data/) (raw CSVs) → [`../analysis/`](../analysis/) (notebook).
- Hardware design rationale → [`decisions/`](decisions/) →
  [`../hardware/flow_monitor.kicad_sch`](../hardware/flow_monitor.kicad_sch).
- Firmware architecture → [`../firmware/README.md`](../firmware/README.md) →
  [`../firmware/STM32CubeIDE/Dripito/Core/`](../firmware/STM32CubeIDE/Dripito/Core/).
- Enclosure fit + Rev-C path → [`enclosure-requirements.md`](enclosure-requirements.md) →
  [`../enclosure/`](../enclosure/) → CAD source in
  [`../hardware/3dmodels/Enclosure/`](../hardware/3dmodels/Enclosure/).
