# hardware/datasheets/

PDF datasheets for every component used in the Dripito monitor BOM,
plus selected supporting documents (controller datasheets, application
notes) referenced from the design.

## Naming convention

- `<MPN>_datasheet.pdf` for the primary datasheet of a single component
  (`STM32G030C8_datasheet.pdf`, `AO3401A_datasheet.pdf`).
- `<part_or_topic>_<descriptor>.pdf` for application notes, controller
  datasheets, or wiring diagrams (`SSD1803A_controller_datasheet.pdf`,
  `DOG_3V3_wiring.pdf`, `EA_DOGS164W-A_extended_datasheet.pdf`).
- Dates in filenames only when multiple revisions of the same datasheet
  are tracked.

## What's currently here

| File | What it is |
|------|------------|
| `STM32G030C8_datasheet.pdf` | Rev-A MCU |
| `TPS610982_datasheet.pdf` | Boost converter (Rev-B power architecture) |
| `AO3401A_datasheet.pdf` | P-channel MOSFET |
| `EA_DOGS164W-A_datasheet.pdf` + `_extended_datasheet.pdf` | LCD module (4×16) |
| `DOG_3V3_wiring.pdf` | LCD wiring reference |
| `SSD1803A_controller_datasheet.pdf` | LCD controller IC; required for the BF-read protocol implemented in firmware |
| `PTS647_datasheet.pdf` | Tactile switches (S1 / S2 / S3 buttons) |
| `competitors/` | Reference material for competing / prior-art devices (e.g. DripAssist) — kept separate so the main folder stays specific to this BOM |

## How to keep this folder current

Use the `digikey` or `element14` skill to fetch up-to-date datasheets
for components present in the schematic. The `bom` skill orchestrates a
sync pass across distributors. Manual additions are fine; just follow
the naming convention above.

When adding a datasheet for a new component:

1. Place it here using the naming convention.
2. Reference the filename from the relevant decision record (e.g.
   `../docs/decisions/comparator-simplification.md`) or from
   `../docs/pcb-design.md`.
3. If the datasheet is application-critical (e.g. LCD controller
   protocol), note that in the firmware code that depends on it as a
   `// see hardware/datasheets/<filename>.pdf §<section>` comment.

## What does **not** belong here

- Product brochures, marketing PDFs, and "click here for more info"
  splash sheets that aren't actual technical references.
- Internal review notes — those go in `../docs/` or in commit messages.
- Datasheets for components considered but rejected — those belong in
  the relevant decision record's "Alternatives considered" section,
  inline as a link or as a downloaded PDF in
  `../docs/decisions/_supporting/` (forthcoming) — not here.
