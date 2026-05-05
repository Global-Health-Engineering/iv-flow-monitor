# Dripito — IV Drip Flow Monitor (Rev-B)

> **Improving a low-cost intravenous infusion flow-rate monitoring device
> for paediatric care in humanitarian healthcare settings.**
> ETH Zürich, Global Health Engineering — semester project, 2026.

A compact, low-power, single-AA-cell IV drip monitor designed for
resource-constrained clinical environments. Custom STM32G0 PCB, optical
dual-beam drop detection, character LCD, piezo alarm, ASA-printed
enclosure with hinged-clamshell chamber holder.

## Motivation

In low-resource hospitals, IV infusion rates are monitored manually by
nursing staff. Errors — especially in paediatric patients — can be fatal.
Commercial monitors are expensive, fragile, and require infrastructure
that is often unavailable. Dripito targets the same clinical task at
roughly two orders of magnitude lower BOM cost, with a deployable form
factor and a fully open hardware / firmware / data stack.

This repository contains the Rev-B development: hardware, firmware,
mechanical design, validation protocol, raw data, and analysis pipeline.

## At a glance

| | |
|---|---|
| **Hardware** | Rev-B PCB, KiCad 8.x, 5 hand-assembled units |
| **MCU** | STM32G071C8TX (Rev-B); STM32G030C8TX (Rev-A baseline) |
| **Detection** | Dual-beam optical, sphere-model volume calibration |
| **Power** | Single AA Li-ion via FFC, TPS610982 boost converter |
| **Enclosure** | ASA white FDM, hinged-clamshell chamber holder, 14–24 mm OD compat |
| **Validation** | 15 Rev-B + 9 Rev-A runs at 20 / 50 / 100 mL/hr |
| **Analysis** | Bland-Altman + train/test MAPE + 95 % LoA, reproducible from raw CSV |
| **Submission** | Target 2026-05-13 |

## Repository layout

```
hardware/      KiCad 8.x project — schematic, PCB, libs, datasheets, gerbers
firmware/      STM32CubeIDE workspaces (InfusionBA Rev-A, InfusionBA2 Rev-B)
enclosure/     Onshape exports, STLs, print profiles, print history
docs/          Written documentation: decisions, requirements, results, limitations
data/          Raw validation CSVs, calibration log, geometry, edge-case logs
analysis/      Reproducible analysis pipeline (Jupyter notebooks + Docker)
media/         Photographs, renders, demo clips
```

Every folder has its own `README.md` documenting what belongs there and
the naming conventions in force. Start with the folder of interest, not
this top-level file.

## Where to upload what

Quick reference — when you have an artefact, where does it go?

| You have | Put it in |
|---|---|
| KiCad schematic / PCB edits | `hardware/` (project files at root) |
| Custom KiCad symbols | `hardware/lib/` |
| Custom KiCad footprints | `hardware/IV_Flow_Monitor_Footprints.pretty/` |
| Component datasheets | `hardware/datasheets/` |
| Re-exported Gerbers + drill + CPL | `hardware/gerbers/` |
| 3D part models for KiCad | `hardware/3dmodels/` |
| Hardware automation scripts | `hardware/scripts/` |
| Firmware code (Rev-B, active) | `firmware/STM32CubeIDE/InfusionBA2/Core/` |
| Firmware code (Rev-A, baseline) | `firmware/STM32CubeIDE/InfusionBA/Core/` |
| Host-runnable firmware tests | `firmware/tests/` (planned) |
| Onshape STEP exports | `enclosure/onshape_exports/` |
| Printer-ready STLs | `enclosure/stl/` |
| Slicer profiles | `enclosure/print_settings/` |
| Print iteration logs | `enclosure/print_history/` (one Markdown file per attempt) |
| Architecture decision (ADR) | `docs/decisions/<topic>.md` (template in `docs/decisions/README.md`) |
| Written reports, specs, narrative | `docs/<topic>.md` |
| Raw validation run CSVs | `data/raw/` (naming pattern in `data/README.md`) |
| Firmware-shakeout (debugging) CSVs | `data/shakeout/` |
| Edge-case observations | `data/edge_cases/EC_XX_YYYY-MM-DD.md` |
| Calibration log row | append to `data/calibration_log.csv` |
| Per-session metadata row | append to `data/session_log.csv` |
| Analysis notebook | `analysis/notebooks/` |
| Generated figures (committed for embedding) | `analysis/figures/` |
| Reusable analysis Python helpers | `analysis/scripts/` |
| Photos, renders, demo clips | `media/` |

If something doesn't fit any of these, the right move is usually
a new folder with its own README explaining the purpose — not a
`misc/` pile.

## Build and flash (firmware)

1. Open `firmware/STM32CubeIDE/InfusionBA2/` in STM32CubeIDE.
2. *Project → Build All*.
3. Connect ST-Link to the SWD header.
4. *Run → Debug*.

Detailed pin maps and the Rev-A baseline build path are in
[`firmware/README.md`](firmware/README.md).

## Reproducing the analysis

The contract: a single command regenerates every figure in
`analysis/figures/` from the raw CSVs in `data/raw/`.

```bash
cd analysis/
docker compose up regenerate-figures
```

For the host-Python path and the sample-data variant (cold-clone test),
see [`analysis/README.md`](analysis/README.md).

## Validation

The validation protocol is **pre-registered**: it is committed to this
repository before any official data is collected. See the commit
timestamp on
[`docs/testing-and-validation.md`](docs/testing-and-validation.md) for the
registration mark. Discard rules and exit criteria are part of the
pre-registration and cannot be re-shaped post-hoc.

The validation campaign runs 2026-05-07 → 2026-05-10:

- **EXP-0** Optical threshold calibration (verification gate: 0 false
  positives in 60 s)
- **EXP-1** Enclosure geometry measurement on all 5 units (basis for
  uncertainty budget)
- **EXP-2** Firmware shakeout with measurable exit criteria
- **EXP-3** 15-run validation matrix at 20, 50, 100 mL/hr
- **EXP-4** 9-run Rev-A baseline under identical conditions
- **EXP-5** 5 pre-defined edge-case scenarios
- **EXP-6** Bland-Altman + train/test MAPE + bootstrap 95 % CI

## Hardware fabrication

PCB: JLCPCB or PCBWay from `hardware/gerbers/`. The companion BOM
generation and supplier sync workflow uses the `bom` skill chained with
`digikey` / `mouser` / `lcsc` skills.

Enclosure: hobbyist-class FDM printer (Prusa, Bambu A1 class) in ASA
white using the profile in `enclosure/print_settings/`. The full
requirements spec — used as the hand-off document for follow-up theses
— is in [`docs/enclosure-requirements.md`](docs/enclosure-requirements.md).

## Citation

A bachelor thesis preceded this Rev-B work:

> Catarci, L. (2025). *Improving a Low-Cost Intravenous Infusion
> Flow-Rate Monitoring Device for Paediatric Care in Humanitarian
> Healthcare Settings*. ETH Zürich, Global Health Engineering.
> DOI: [10.5281/zenodo.16902366](https://doi.org/10.5281/zenodo.16902366).

The Rev-B work documented in this repository receives its own Zenodo
DOI on submission *(populated at submission)*.

## License

- **Code, firmware, documentation, and validation data:**
  [CC BY 4.0](LICENSE-CC-BY-4.0.md).
- **Hardware design files (KiCad project, custom symbols, the bulk of
  custom footprints):** [CERN OHL 2.0 Permissive](LICENSE-CERN-OHL-2-PERMISSIVE.md).
- **Three specific custom footprints** are licensed under
  [CC BY-SA 4.0](LICENSE-CC-BY-SA-4.0.md):
  `SW_HYP_1TS005F-2500-5001`,
  `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal`,
  `X_SW_Slide_SPDT_SSK12D07VG5`. See
  [`hardware/IV_Flow_Monitor_Footprints.pretty/README.md`](hardware/IV_Flow_Monitor_Footprints.pretty/README.md).
- Generated CubeMX/HAL code retains its
  `Copyright (c) STMicroelectronics` headers.

## Author and supervision

**Leandro Catarci** — MSc Mechanical Engineering, ETH Zürich.
Semester project at ETH Global Health Engineering, 2026.

Supervisors: Jakub Tkaczuk (lead), Bettina Melberg.
External clinical input: Janis Tupesis (WHO Emergency Medical Teams).

---

*Dripito — because the right drop rate saves lives.*
