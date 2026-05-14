# Dripito — IV Drip Flow Monitor (Rev-B)

> Improving a low-cost intravenous infusion flow-rate monitoring device
> for paediatric care in humanitarian healthcare settings.
> ETH Zürich, Global Health Engineering — semester project, 2026.

A single-AA-cell IV drip monitor for resource-constrained clinical
environments. Custom STM32G0 PCB, optical dual-beam drop detection,
monochrome graphic LCD, piezo alarm, ASA-printed enclosure with
gear-driven broom-holder chamber clamp.

### → Full project page: **[gluflex.github.io/dripito](https://gluflex.github.io/dripito)**

[![Build & test](https://github.com/Gluflex/dripito/actions/workflows/build-and-test.yml/badge.svg?branch=v2)](https://github.com/Gluflex/dripito/actions/workflows/build-and-test.yml)
[![Deploy site to GitHub Pages](https://github.com/Gluflex/dripito/actions/workflows/deploy-site.yml/badge.svg?branch=v2)](https://github.com/Gluflex/dripito/actions/workflows/deploy-site.yml)

Interactive dual-beam simulation, clickable PCB architecture, validation results, architecture decisions, assembly guide. This README covers only the essentials for cloning, building, and reproducing.

## At a glance

| | |
|---|---|
| **MCU** | STM32G071C8TX |
| **Hardware** | Rev-B PCB, KiCad 8.x, hand-assembled |
| **Detection** | Dual-beam optical, sphere-model volume calibration |
| **Power** | Single AA Li-ion via FFC, TPS610981 boost converter |
| **Enclosure** | ASA white FDM, sliding-gear chamber holder — Rev-B integrates the assembly for testing; full mechanical rework expected for Rev-C |
| **Validation** | 21 paired bench runs against gravimetric truth across 3 sessions (5 V_50 calibration + 11 position-drift + 5 raw-waveform), macro-20 drip set |
| **BOM** | ~CHF 39, single-qty (see project page) |
| **Submission** | 2026-05-14 |

## Reproduce the analysis

One command, on a clean machine with Docker:

```bash
cd analysis/
docker compose up regenerate-figures-sample   # cold-clone test (sample data)
docker compose up regenerate-figures          # real campaign data
```

Pipeline source: [`analysis/notebooks/validation.ipynb`](analysis/notebooks/validation.ipynb).
Dependencies hash-locked in [`analysis/requirements.txt`](analysis/requirements.txt).
Protocol: [`docs/testing-and-validation.md`](docs/testing-and-validation.md).

## Build the firmware

1. Open `firmware/STM32CubeIDE/InfusionBA2/` in STM32CubeIDE.
2. *Project → Build All*.
3. Connect ST-Link, *Run → Debug*.

Pin maps in [`firmware/README.md`](firmware/README.md).

## Hardware fabrication

PCB from `hardware/gerbers/` (JLCPCB / PCBWay).

Enclosure: STEP and STL exports in [`hardware/3dmodels/Enclosure/`](hardware/3dmodels/Enclosure/) (source CAD in Onshape). The current Rev-B enclosure is **not the final mechanical design** — it integrates the PCB + chamber holder + optics + battery into a testable assembly so the rest of the device can be validated. A full mechanical rework is expected for Rev-C. See [`docs/decisions/chamber-holder-mechanism.md`](docs/decisions/chamber-holder-mechanism.md), [`docs/decisions/sensor-arm-alignment.md`](docs/decisions/sensor-arm-alignment.md), and [`docs/enclosure-requirements.md`](docs/enclosure-requirements.md) for the rationale and Rev-C path.

## Repository layout

```
hardware/        KiCad 8.x project — schematic, PCB, libs, datasheets, gerbers, 3D models (PCB + Enclosure)
firmware/        STM32CubeIDE workspace (InfusionBA2 Rev-B)
enclosure/       Rev-B-is-not-final framing + cross-references; CAD lives in hardware/3dmodels/Enclosure/
docs/            Architecture decisions, requirements, results, limitations
data/            Raw validation CSVs, UART logs, gravimetric scale streams, geometry, edge cases
analysis/        Reproducible analysis pipeline (Docker + Jupyter) + diagnostic plotters + figures
tools/           Bench helpers (UART logging, scale logging, position-overlay rendering)
site/            GitHub Pages source (Astro)
media/           Photos, renders, demo clips
HANDOVER.md      State-of-the-prototype handover (Rev-B → Rev-C, what works / blockers / path)
CONTRIBUTING.md  Contribution guidelines (PRs paused during grading)
```

Each folder has its own `README.md`.

For the next person picking this up, start with [`HANDOVER.md`](HANDOVER.md): what works in Rev-B scope, the three blockers (position-dependence, drop-shape oscillation, tilt sensitivity), and the Rev-C optical-front-end path. [`docs/limitations.md`](docs/limitations.md) §17 is the matching architectural finding with bench evidence.

## Citation

A bachelor thesis preceded this work:

> Catarci, L. (2025). *Improving a Low-Cost Intravenous Infusion Flow-Rate Monitoring Device for Paediatric Care in Humanitarian Healthcare Settings*. ETH Zürich, Global Health Engineering. DOI: [10.5281/zenodo.16902366](https://doi.org/10.5281/zenodo.16902366).

The Rev-B work in this repository will receive its own Zenodo DOI: *10.5281/zenodo.TBD — minted post-submission*.

## License

- Code, firmware, docs, data: [CC BY 4.0](LICENSE-CC-BY-4.0.md)
- Hardware (KiCad project, custom symbols, most footprints): [CERN OHL 2.0 Permissive](LICENSE-CERN-OHL-2-PERMISSIVE.md)
- Three specific custom footprints: [CC BY-SA 4.0](LICENSE-CC-BY-SA-4.0.md) — see [`hardware/IV_Flow_Monitor_Footprints.pretty/README.md`](hardware/IV_Flow_Monitor_Footprints.pretty/README.md)
- CubeMX/HAL files retain `Copyright (c) STMicroelectronics` headers.

## Author and supervision

**Leandro Catarci** — MSc Mechanical Engineering, ETH Zürich. Semester project at ETH Global Health Engineering, 2026.

**Jakub Tkaczuk** — Supervisor.
**Prof. Elizabeth Tilley** — Group head, Chair of Global Health Engineering, ETH Zürich.
