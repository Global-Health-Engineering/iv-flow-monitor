# 2026-05-14 PM — raw beam waveform capture across mount positions

First Dripito bench session to capture the **raw photodiode waveforms** (not just edge-time pulse durations) across mount positions where K-fit broke yesterday. The new dimension this dataset adds is shape information — rise/fall asymmetry, multi-peak structure, area-under-attenuation, umbilical/splash signatures — that the threshold-time analysis used through 2026-05-13 cannot access. Captures support the Phase 2 offline algorithm exploration in `analysis/scripts/algo_replay.py`, `analysis/scripts/algo_breadth_pass.py`, and `analysis/scripts/fit_final_algorithm.py`.

Firmware: `feat/raw-capture-rev-c` (branched from `v2`, not merged into Rev-B submission firmware — submission firmware = `v2` HEAD). Adds compile-time `ENABLE_RAW_CAPTURE=1`, sample-time `ADC_SAMPLETIME_160CYCLES_5` (160.5 cycles; an earlier 3.5-cycle attempt was reverted when the photodiode TIA didn't settle and runtime reads dropped ~10 % below boot-cal), polled register-level pair-read, 8 kB ring buffer (1024 × 8 B), 921600 baud UART (the 2 Mbps plan was reverted with the buffer halving), per-drop CSV dump on accept.

UART format addition (the rest of the schema is unchanged from `docs/results.md` references):

```
DROP_RAW_BEGIN,<t_ms>,<drop_N>,<sample_count>,<t_first_us>,<t_last_us>,<t_trigger_us>
RAW,<t_us>,<top_adc>,<bot_adc>        × sample_count rows
DROP_RAW_END,<drop_N>
```

`t_us` is the free-running TIM2 µs counter (1 MHz, 32-bit wrap-safe). `t_trigger_us` is the t_us at the TOP-entry (tT_in) edge.

## Captures

All captures at the same drip set (macro 20 gtt/mL), water, board 1, flow ≈ 50 mL/h via roller-clamp setting. Position is measured relative to the V_50_05-era canonical mount (the same mount used during the morning calibration campaign).

| Tag                              | Position             | Has scale.csv | Role                                       |
|----------------------------------|----------------------|---------------|--------------------------------------------|
| `p1_high_capture.log`            | canonical V_50_05-era| no            | First-light raw-byte capture (pre-format)  |
| `p1_high_first_capture.uart.log` | canonical            | no            | Initial UART format-validation probe       |
| `p1_high_run01.uart.log`         | canonical            | no            | Warm-up run                                |
| `p1_high_run02.uart.log`         | canonical            | **yes**       | Gravimetric-paired primary at p1           |
| `p2_minus1mm_run01.uart.log`     | 1 mm below canonical | no            | Warm-up after remount                      |
| `p2_minus1mm_run02.uart.log`     | 1 mm below canonical | **yes**       | Gravimetric-paired primary at p2           |
| `p3_minus4mm_run01.uart.log`     | 4 mm below canonical | **yes**       | Gravimetric-paired (only run at p3)        |

The three `*_run02.uart.log` and the `p3_*_run01.uart.log` are the algorithm-evaluation set; the `*_first_*` / `*_run01` captures at p1 and p2 are warm-ups and exist to confirm steady-state behaviour before paired-with-scale acquisition began.
