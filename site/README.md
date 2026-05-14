# Dripito — GitHub Pages site

Astro-based static site for the Dripito open-source IV drip flow monitor. Single landing page composing every section: dual-beam architecture animation, real PCB layout (extracted from the KiCad project), analysis + validation results, architecture decisions, BOM with qty=1 / qty=1000 toggle, limitations, and an assembly walkthrough.

## Local development

```bash
npm install
npm run dev          # http://localhost:4321
npm run build        # static output to dist/
npm run preview      # preview the production build locally
```

## Deploy to GitHub Pages

The [`.github/workflows/deploy-site.yml`](../.github/workflows/deploy-site.yml) workflow builds and deploys on every push to `v2`. GitHub Pages source must be set to **GitHub Actions** in the repository settings.

`astro.config.mjs` sets `site` to the canonical Pages URL and `base` to `/dripito/`.

## Source structure

```
src/
├── layouts/Base.astro            # html/head/body shell, global CSS, OG/Twitter meta
├── pages/index.astro             # landing page — composes the components
├── components/
│   ├── Nav.astro
│   ├── Hero.astro
│   ├── Problem.astro
│   ├── DualBeam.astro            # animated SVG + live readout
│   ├── PCBArchitecture.astro     # real PCB SVG from KiCad + ADR-linked hotspots
│   ├── PowerTree.astro
│   ├── StateMachine.astro
│   ├── Analysis.astro            # bench-overlay error-budget figure
│   ├── Decisions.astro           # ADR card grid
│   ├── BuildItYourself.astro     # BOM table (CSV-driven, qty toggle)
│   ├── Assembly.astro            # step-by-step build cards
│   ├── Limitations.astro         # top-N limitations surface
│   ├── OpenQuestions.astro
│   └── Footer.astro
└── styles/global.css             # design tokens + all section styles
```

## Where the PCB SVG comes from

The PCB diagram in `PCBArchitecture.astro` was generated from the live KiCad project at `hardware/flow_monitor.kicad_pcb` via the `kicad` skill. To regenerate after a layout change:

1. Run the analyser against the `.kicad_pcb` file to emit `pcb_analysis.json`.
2. Run the build script that converts the analysis into the SVG fragment.
3. Paste the SVG into `src/components/PCBArchitecture.astro`.

## BOM data source

`BuildItYourself.astro` reads [`../hardware/bom.csv`](../hardware/bom.csv) at build time and renders it as a 6-column grouped table with a qty=1 / qty=1000 pill toggle and per-group collapse. Editing the CSV is enough to update the rendered table — no component-side changes required.
