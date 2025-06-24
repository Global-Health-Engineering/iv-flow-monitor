# Dripito – Pediatric IV Flow Rate Monitor

This repository contains the firmware and altium files for the development of **Dripito**, a pediatric IV flow rate monitor designed for humanitarian and low-resource settings.

## Project Overview

Dripito is developed as part of a Bachelor's thesis at ETH Zurich in collaboration with the Global Health Engineering group. The project aims to create a reliable, low-cost device capable of accurately detecting IV flow rates using drop sensing and IR technology.

## Structure

- `/firmware/` — STM32 firmware source code and configuration (CubeMX `.ioc` file)
- `/hardware/` — PCB schematics, layouts (Altium files), and BoM
- `/data/` — Experimental logs (no raw data if private)
- `/docs/` — System architecture, design rationale, photos
- `/testing/` — Test scripts and evaluation notes

## Quick Start

```bash
git clone https://github.com/Global-Health-Engineering/dripito.git
cd dripito/firmware
# build or flash via STM32CubeIDE / CLI

## Milestones

- ✅ Schematic and PCB design finalized  
- ✅ Initial firmware structure and button interface  
- ✅ Basic drop sensing and IR LED control  
- ☐ Full system integration and casing assembly  
- ☐ Calibration and experimental validation  
- ☐ Final documentation and ETH submission  
- ☐ Optional open hardware release

## Authors

- **Leandro Catarci** – Bachelor student, ETH Zürich
- **Rebecca Jean Alcock** – Co-Supervisor, Global Health Engineering  
- **Dr. Jakub Tkaczuk** – Co-Supervisor, Global Health Engineering  
- **Prof. Elizabeth Tilley** – Thesis Advisor, ETH Zürich
- **Dr. Michelle Niescierenko (Harvard)

## License

All code and documentation in this repository is provided for academic and research purposes under the supervision of ETH Zürich.  
License terms will be finalized upon project completion.  
Please contact the authors before reuse or redistribution.
