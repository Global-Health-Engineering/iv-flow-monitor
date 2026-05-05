# media/

Photographs, renders, and short demo clips of the Dripito monitor —
the visual material that is embedded in the top-level `README.md`,
`docs/results.md`, and `docs/enclosure.md`, plus any presentation or
publication assets.

## Contents

| File | What it is |
|------|------------|
| `pcb.jpg` | Photograph of the assembled PCB |
| `schematic.jpg` | Rendered schematic snapshot |
| `3dmodel_front.jpg` | Front view of the 3D model render |
| `3dmodel_back.jpg` | Back view of the 3D model render |

## Naming convention

- Lowercase kebab-case for stable assets:
  `assembled-device-front.jpg`, `enclosure-cross-section.png`.
- For dated / iteration shots (bench photos, print attempts):
  `YYYY-MM-DD_<short-description>.jpg` — date prefix lets `ls` order
  by capture day naturally.
- Renders include `_render` in the filename so they don't get confused
  with photographs (e.g. `assembled-device-front_render.png`).

## Format and resolution

- Photographs: JPEG, max edge ≤ 2048 px, ~80 % quality. Embed at the
  display size you actually need; do not commit 24 MP originals.
- Renders: PNG when transparency or sharp edges matter (UI mockups,
  schematic renders), JPEG otherwise.
- Animated demos: MP4 (H.264) preferred over GIF for file-size
  reasons. ≤ 5 MB per clip; longer demos go on Zenodo / YouTube and
  are linked from the README.

## What does not belong here

- Slide decks (`.pptx`, `.key`) — those go in
  `../docs/presentations/` if added.
- Photos containing identifiable patient information or clinical
  imagery without consent. None expected.
- Working files (Photoshop `.psd`, source video projects). Commit only
  the exported asset.
- Internal print-history photos for enclosure iterations — those go in
  `../enclosure/print_history/` next to the matching log entry.

## Embedding from Markdown

```markdown
![Assembled Dripito monitor](media/assembled-device-front.jpg)
```

Use relative paths so embedding works on GitHub, locally, and in the
planned GitHub Pages site.
