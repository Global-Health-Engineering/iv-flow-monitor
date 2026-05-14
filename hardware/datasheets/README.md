# hardware/datasheets/

PDF datasheets for every component on the Dripito BOM, plus selected
controller datasheets and application notes referenced from the design.

## Naming convention

- `<MPN>_datasheet.pdf` for the primary datasheet of a component
  (`STM32G030C8_datasheet.pdf`, `AO3401A_datasheet.pdf`).
- `<part_or_topic>_<descriptor>.pdf` for application notes, controller
  datasheets, or wiring diagrams (`SSD1803A_controller_datasheet.pdf`,
  `DOG_3V3_wiring.pdf`).

## What's currently here

| File | What it is |
|------|------------|
| `STM32G030C8_datasheet.pdf` | Rev-A MCU (kept for reference; Rev-B uses STM32G071C8 — datasheet not duplicated here, see [ST product page](https://www.st.com/en/microcontrollers-microprocessors/stm32g071c8.html)) |
| `TPS610981_datasheet.pdf` | TPS61098-family boost converter — Rev-B uses the TPS610981 variant per the schematic (see [`../../docs/decisions/power-architecture.md`](../../docs/decisions/power-architecture.md)). The PDF is the joint datasheet for the TPS61098, TPS610981, and TPS610982 voltage variants. |
| `AO3401A_datasheet.pdf` | P-channel MOSFET |
| `EA_DOGS164W-A_datasheet.pdf` + `_extended_datasheet.pdf` | LCD module (4×16) |
| `DOG_3V3_wiring.pdf` | LCD wiring reference |
| `SSD1803A_controller_datasheet.pdf` | LCD controller IC; required for the BF-read protocol |
| `PTS647_datasheet.pdf` | Tactile switches (S1 / S2 / S3 buttons) |
| `competitors/` | Reference material for prior-art devices (DripAssist) |

## What does **not** belong here

- Product brochures and marketing PDFs that aren't actual technical references.
- Datasheets for components considered but rejected — those belong in
  the relevant decision record, not here.
