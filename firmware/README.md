# firmware/

Embedded C firmware for the STM32-based Dripito monitor. Two coexisting
CubeIDE projects sit under `STM32CubeIDE/` — they target different MCUs
and different hardware revisions and are **not interchangeable**. Choose
deliberately based on which board you are flashing.

## Layout

```
firmware/
├── STM32CubeIDE/
│   ├── InfusionBA/              # Rev-A / v2 — STM32G030C8TX
│   ├── InfusionBA2/             # Rev-B / power-arch-v2 — STM32G071C8TX
│   ├── InfusionBA.ioc           # CubeMX config (legacy companion to InfusionBA)
│   ├── STM32G030C8TX_FLASH.ld   # legacy linker script
│   ├── Core/                    # legacy generated tree
│   ├── Drivers/                 # legacy HAL drop-in
│   └── boot_sound_preview.html  # bench scratch (gitignored)
└── tests/                       # planned — host-runnable C unit tests for CI
```

`STM32CubeIDE/InfusionBA2/` is the active firmware for Rev-B validation.
`STM32CubeIDE/InfusionBA/` remains in tree because EXP-4 (Rev-A baseline,
see `../docs/testing-and-validation.md`) flashes it for the comparative
measurement and the commit hash is part of that experiment's evidence.

## Build & flash

Build is **STM32CubeIDE GUI only** — no CLI build is configured.

1. Open the relevant project in STM32CubeIDE (File → Import → Existing
   Projects into Workspace, point at `firmware/STM32CubeIDE/InfusionBA2/`
   or `firmware/STM32CubeIDE/InfusionBA/`).
2. To regenerate HAL code from a peripheral config change, open the
   project's `.ioc` (CubeMX) and click *Generate Code*. STMicroelectronics
   copyright headers in generated files must be preserved — they are
   reapplied on regeneration.
3. Build: *Project → Build All*.
4. Flash via ST-Link: *Run → Debug*.

## Project comparison

| Project | MCU | Linker | Hardware rev | Drop detection | Buttons |
|---------|-----|--------|--------------|----------------|---------|
| `InfusionBA/` | STM32G030C8TX | `STM32G030C8TX_FLASH.ld` | Rev-A / v2 | EXTI on `DROP_INT` (PB10) + ADC on `PD_ADC` (PA3) | MINUS / PLUS / MODE / MUTE on PB9 / PB8 / PB7 / PB6 |
| `InfusionBA2/` | STM32G071C8TX | `STM32G071C8TX_FLASH.ld` | Rev-B / power-arch-v2 | Dual photodiodes `ADC_IR_DETECTOR_TOP` (PA1) + `ADC_IR_DETECTOR_BOT` (PA4); dual LED drivers `LED_CTRL_TOP` (PB3) + `LED_CTRL_BOT` (PB4) | MUTE / MODE / RES on PB6 / PB7 / PB8 |

Pin definitions are the source of truth in each project's
`Core/Inc/main.h`. When in doubt, read the header — same filename in both
projects, different pins.

## Recurring CubeIDE pitfalls

- The `.metadata/`, `.settings/`, `.cproject`, `.project`, `Debug/`,
  `Release/`, and `*.launch` files are **machine-specific** and gitignored
  at the repo root. Do not commit them.
- The CubeIDE workspace inside `STM32CubeIDE/` is the IDE's working
  directory, not just the project sources. Treat it as a workspace folder.
- Editing peripheral config without regenerating the `.ioc` will silently
  desync the HAL init code from the documented configuration.

## Planned: host-runnable unit tests + CI

`firmware/tests/` is currently a stub. The Week-4 polish sprint
(see `../docs/project-planning.md`, forthcoming) adds:

- C unit tests for drop-detection edge logic and calibration math, with
  a mock HAL so they compile + run on a host (not the MCU)
- A GitHub Actions workflow that builds the firmware (cross-compile via
  `arm-none-eabi-gcc` in CI) and runs the unit tests on every push
- A green CI badge in the top-level README

The firmware itself does not need to know about any of this — the tests
include the relevant headers as a host build with HAL stubs.

## License

Generated CubeMX/HAL code retains its original `Copyright (c) YYYY
STMicroelectronics` headers. Hand-written code in `Core/Src/` is covered
by the repo's primary license — see `../LICENSE-CC-BY-4.0.md`.
