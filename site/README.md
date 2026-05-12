# Dripito — GitHub Pages site

Astro-based static site for the Dripito open-source IV drip flow monitor. Single landing page with the dual-beam architecture animation, the real PCB layout (extracted from the KiCad project), validation summary, and downloads.

## Local development

```bash
npm install
npm run dev          # http://localhost:4321
npm run build        # static output to dist/
npm run preview      # preview the production build locally
```

## Deploy to GitHub Pages

The `.github/workflows/deploy.yml` workflow builds and deploys on every push to `main`. To enable:

1. In the repo settings, set **Pages → Source** to **GitHub Actions**.
2. Adjust `astro.config.mjs`:
   - `site`: your canonical URL (e.g. `https://gluflex.github.io`)
   - `base`: `/<repo-name>` if served from a sub-path, or `/` for a root/custom domain.
3. Push to `main`. The workflow runs `npm ci && npm run build`, uploads `dist/`, and deploys.

## Source structure

```
src/
├── layouts/Base.astro        # html/head/body shell, global CSS import
├── pages/index.astro         # landing page — composes the components
├── components/
│   ├── Nav.astro
│   ├── Hero.astro
│   ├── Problem.astro
│   ├── DualBeam.astro        # animated SVG + live readout
│   ├── PCBArchitecture.astro # real PCB SVG from KiCad + 7 hotspots
│   ├── PowerTree.astro
│   ├── StateMachine.astro
│   ├── Validation.astro
│   ├── BuildItYourself.astro
│   └── Footer.astro
└── styles/global.css         # design tokens + all section styles
```

## Where the PCB SVG comes from

The PCB diagram in `PCBArchitecture.astro` was generated from the live KiCad project at `D:\Dripito\github\hardware\flow_monitor.kicad_pcb` via the `kicad` skill. To regenerate after a layout change:

1. Re-run the analyser: `python3 <kicad-skill>/scripts/analyze_pcb.py flow_monitor.kicad_pcb --output pcb_analysis.json`
2. Re-run `D:\Dripito\build_pcb_svg.py` to emit the SVG fragment.
3. Paste the SVG into `src/components/PCBArchitecture.astro`.

## Replacing placeholders

Items currently marked as placeholders (yellow hatched zones) or pending real assets:

- Hero photo (`src/components/Hero.astro` → image placeholder)
- Tupesis quote — fabricated illustrative copy, NOT real correspondence (yellow border)
- Schematic snippet thumbnails inside each PCB hotspot side-panel
- Download links to KiCad / STL / firmware / Zenodo
- Real values for Bland-Altman scatter and MAPE table

Once validation lands clean (target 2026-05-10), swap the placeholders for real assets.
