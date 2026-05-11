# Dripito — IV Drip Flow Monitor (Rev-B)

> Improving a low-cost intravenous infusion flow-rate monitoring device
> for paediatric care in humanitarian healthcare settings.
> ETH Zürich, Global Health Engineering — semester project, 2026.

A single-AA-cell IV drip monitor for resource-constrained clinical
environments. Custom STM32G0 PCB, optical dual-beam drop detection,
monochrome graphic LCD, piezo alarm, ASA-printed enclosure with
gear-driven broom-holder chamber clamp.

### → Full project page: **[gluflex.github.io/iv-flow-monitor-v2](https://gluflex.github.io/iv-flow-monitor-v2)**

Interactive dual-beam simulation, clickable PCB architecture, validation results, architecture decisions, assembly guide. This README covers only the essentials for cloning, building, and reproducing.

## At a glance

| | |
|---|---|
| **MCU** | STM32G071C8TX |
| **Hardware** | Rev-B PCB, KiCad 8.x, hand-assembled |
| **Detection** | Dual-beam optical, sphere-model volume calibration |
| **Power** | Single AA Li-ion via FFC, TPS610982 boost converter |
| **Enclosure** | ASA white FDM, gear-driven broom-holder chamber clamp |
| **Validation** | 21 runs vs gravimetric ground truth, 3 flow rates × macro-20 |
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

PCB from `hardware/gerbers/` (JLCPCB / PCBWay). Enclosure printed in ASA white per the profile in `enclosure/print_settings/`. Full enclosure requirements (hand-off for follow-up work) in [`docs/enclosure-requirements.md`](docs/enclosure-requirements.md).

## Repository layout

```
hardware/    KiCad 8.x project — schematic, PCB, libs, datasheets, gerbers
firmware/    STM32CubeIDE workspace (InfusionBA2 Rev-B)
enclosure/   Onshape exports, STLs, print profiles, print history
docs/        Architecture decisions, requirements, results, limitations
data/        Raw validation CSVs, calibration log, geometry, edge cases
analysis/    Reproducible analysis pipeline (Docker + Jupyter)
tools/       Bench helpers (e.g. gravimetric log logger)
media/       Photos, renders, demo clips
```

Each folder has its own `README.md`.

## Citation

A bachelor thesis preceded this work:

> Catarci, L. (2025). *Improving a Low-Cost Intravenous Infusion Flow-Rate Monitoring Device for Paediatric Care in Humanitarian Healthcare Settings*. ETH Zürich, Global Health Engineering. DOI: [10.5281/zenodo.16902366](https://doi.org/10.5281/zenodo.16902366).

The Rev-B work in this repository receives its own Zenodo DOI on submission *(populated at submission)*.

## License

- Code, firmware, docs, data: [CC BY 4.0](LICENSE-CC-BY-4.0.md)
- Hardware (KiCad project, custom symbols, most footprints): [CERN OHL 2.0 Permissive](LICENSE-CERN-OHL-2-PERMISSIVE.md)
- Three specific custom footprints: [CC BY-SA 4.0](LICENSE-CC-BY-SA-4.0.md) — see [`hardware/IV_Flow_Monitor_Footprints.pretty/README.md`](hardware/IV_Flow_Monitor_Footprints.pretty/README.md)
- CubeMX/HAL files retain `Copyright (c) STMicroelectronics` headers.

## Author and supervision

**Leandro Catarci** — MSc Mechanical Engineering, ETH Zürich. Semester project at ETH Global Health Engineering, 2026.

**Jakub Tkaczuk** — Supervisor.
**Prof. Elizabeth Tilley** — Group head, Chair of Global Health Engineering, ETH Zürich.
