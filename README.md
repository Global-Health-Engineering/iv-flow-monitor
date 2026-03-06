# Dripito — IV Flow Monitor v2

> **Improving a Low-Cost Intravenous Infusion Flow Rate Monitoring Device for Paediatric Care in Humanitarian Healthcare Settings**

A compact, low-power IV drip rate monitor designed for use in resource-constrained humanitarian settings. Built around an STM32G0 microcontroller with an optical drop sensor, LCD display, buzzer alarm, and USB-C power — all on a custom PCB.

---

## 🎯 Motivation

In low-resource hospitals, IV infusion rates are often monitored manually by nursing staff. Errors in flow rate — especially in paediatric patients — can be fatal. Commercial monitors are expensive, fragile, and require infrastructure. Dripito aims to be cheap, rugged, and deployable anywhere.

This repository contains the full v2 development: firmware, hardware design, analysis, and testing data from the bachelor thesis.

---

## 📁 Repository Structure

```
iv-flow-monitor-v2/
├── src/                    # STM32CubeIDE firmware project
│   ├── Core/               # HAL-generated init, IRQ handlers
│   │   ├── Src/
│   │   │   ├── main.c
│   │   │   ├── dripito_app.c   # Core application logic
│   │   │   ├── alarm.c         # Alarm thresholds & logic
│   │   │   ├── buzzer.c        # Piezo buzzer driver
│   │   │   ├── lcd.c           # LCD driver
│   │   │   └── ui.c            # User interface state machine
│   │   └── Inc/            # Header files
│   ├── Drivers/            # STM32 HAL + BSP drivers
│   ├── User/               # Custom fonts, GUI assets, config
│   └── InfusionBA.ioc      # STM32CubeMX config file
├── hardware/
│   ├── design/             # KiCad schematics & PCB layout
│   └── testing/            # Hardware test records
├── analysis/               # Data analysis scripts & results
├── data/                   # Raw measurement data
└── media/                  # Photos, renders, demo videos
```

---

## 🔧 Hardware

| Component | Details |
|---|---|
| MCU | STM32G030C8T — ARM Cortex-M0+, 64KB flash |
| Display | Monochrome LCD (custom driver) |
| Sensor | Optical drop counter (IR emitter + receiver) |
| Alarm | Piezo buzzer |
| Power | USB-C (5V), low-power sleep modes |
| PCB | Custom KiCad design, 2-layer |

---

## 💻 Firmware

Built with **STM32CubeIDE** (C, HAL). Key modules:

- **`dripito_app.c`** — Main application: drop counting, flow rate calculation, alarm logic
- **`ui.c`** — State machine for user interface (set target rate, display live rate, alarm states)
- **`alarm.c`** — Configurable thresholds for over/under-rate alerts
- **`lcd.c` / `buzzer.c`** — Peripheral drivers

### Build & Flash

1. Open `src/InfusionBA.ioc` in **STM32CubeMX** or import the project into **STM32CubeIDE**
2. Build: `Project → Build All`
3. Flash via ST-Link: `Run → Debug` or use `openocd`

```bash
# Flash via openocd (if configured)
openocd -f interface/stlink.cfg -f target/stm32g0x.cfg \
  -c "program build/InfusionBA.elf verify reset exit"
```

---

## 📊 Analysis

The `analysis/` directory contains Python/MATLAB scripts used to evaluate sensor accuracy, flow rate estimation error, and alarm response time across tested IV sets and drop sizes.

---

## 📄 License

**Code & Documentation:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

**License Exceptions (CC BY-SA 4.0):**
- `hardware/design/IV_Flow_Monitor_Footprints.pretty/SW_HYP_1TS005F-2500-5001.kicad_mod`
- `hardware/design/IV_Flow_Monitor_Footprints.pretty/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.kicad_mod`
- `hardware/design/IV_Flow_Monitor_Footprints.pretty/X_SW_Slide_SPDT_SSK12D07VG5.kicad_mod`

---

## 👤 Author

**Leandro Catarci** — BSc Mechanical Engineering, ETH Zürich
Bachelor Thesis, 2025 | Semester Project (v2), 2026

---

*Dripito — because the right drop rate saves lives.*
