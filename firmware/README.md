# firmware/

Embedded C firmware for the Dripito Rev-B monitor. Single CubeIDE
project at `STM32CubeIDE/InfusionBA2/`, targeting **STM32G071C8TX**.

A Rev-A predecessor (STM32G030C8TX, hardware revision A) lives in the
bachelor-thesis archive on Zenodo
([10.5281/zenodo.16902366](https://doi.org/10.5281/zenodo.16902366));
this repository ships only the active Rev-B firmware.

## Build & flash

CubeIDE GUI only — no CLI build is configured.

1. *File → Import → Existing Projects into Workspace* — point at
   `firmware/STM32CubeIDE/InfusionBA2/`.
2. To regenerate HAL after a peripheral config change, open
   `InfusionBA2.ioc` and click *Generate Code*. Preserve any
   `Copyright (c) STMicroelectronics` headers — they are reapplied on
   regeneration.
3. *Project → Build All*.
4. Connect ST-Link, *Run → Debug*.

## Pin map highlights

| Function | Pin |
|---|---|
| IR detector top / bottom | PA1 / PA4 (`ADC_IR_DETECTOR_TOP/BOT`) |
| LED driver top / bottom | PB3 / PB4 (`LED_CTRL_TOP/BOT`) |
| Battery sense | PB2 (`ADC_V_BAT`) |
| Buzzer PWM | PA8 (`BUZZER_CTRL`) |
| Buttons (MUTE / MODE / RES) | PB6 / PB7 / PB8 |
| UART (debug) | PA9 / PA10 |

Source of truth: `STM32CubeIDE/InfusionBA2/Core/Inc/main.h`.

## CubeIDE pitfalls

- `.metadata/`, `.settings/`, `.cproject`, `.project`, `Debug/`,
  `Release/`, and `*.launch` are machine-specific and gitignored.
- Editing peripheral config without regenerating the `.ioc` will
  silently desync HAL init from the documented configuration.

## License

Generated CubeMX/HAL code retains its `Copyright (c) STMicroelectronics`
headers. Hand-written code in `Core/Src/` is covered by
[`../LICENSE-CC-BY-4.0.md`](../LICENSE-CC-BY-4.0.md).
