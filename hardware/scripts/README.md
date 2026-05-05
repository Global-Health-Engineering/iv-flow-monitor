# hardware/scripts/

Hardware-side automation. Currently a single script for converting
PNG / JPG logos into KiCad silkscreen footprints, plus the source
artwork it consumes.

## Contents

| File | Purpose |
|------|---------|
| `logo_to_footprint.py` | Rasterises a logo image into a KiCad `.kicad_mod` footprint on F.SilkS, using `fp_poly` rectangles. Enforces the ≥ 0.2 mm minimum feature size required by JLCPCB silkscreen. Uses PIL + numpy. |
| `eth_logo.png` | ETH Zürich logo source artwork |
| `ghe_logo.jpg` | Global Health Engineering logo source artwork |

## Usage

```bash
cd hardware/scripts
python logo_to_footprint.py --input eth_logo.png \
                            --output ../IV_Flow_Monitor_Footprints.pretty/ETH_Zurich_Logo.kicad_mod \
                            --pixel-size 0.2
```

(Exact CLI may vary — read the script for the argument set it
actually accepts.)

The output footprints live in `../IV_Flow_Monitor_Footprints.pretty/`.
Regenerate them rather than hand-editing if the source artwork
changes; the script enforces silkscreen design rules so manual
editing risks producing non-fab-able geometry.

## Conventions

- Python 3 with `pillow` (PIL) and `numpy` as the only non-stdlib
  dependencies. Keep this folder dependency-light — install via system
  Python or a one-off venv; do not introduce a `requirements.txt` here
  (the analysis pipeline's pinning lives at `../../analysis/` instead).
- One script per task. If a second tool is added (e.g. a BOM diff
  helper), it gets its own file rather than expanding `logo_to_footprint.py`.
- Output destinations are passed as CLI arguments, not hard-coded —
  each script must run cleanly from the repo root or from inside this
  folder.

## What does not belong here

- Firmware build / flash scripts (those would go under
  `../../firmware/scripts/` if added).
- Analysis-pipeline code (lives at `../../analysis/scripts/`).
- Bytecode / `__pycache__/` (gitignored).
