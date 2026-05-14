# 2026-05-13 PM — position-dependence campaign

Eleven 60–65 s gravimetric runs captured the afternoon following the V_50_01..05 morning campaign, with the device deliberately remounted between groups of runs to probe the algorithm's behaviour across mount geometries. The runs underpin the position-dependence finding documented in `docs/limitations.md` §Position-dependence.

| Tag | Firmware | Position | Drops | Scale Δ (mL) | LCD sum (mL) | Error % | Comment |
|---|---|---|---:|---:|---:|---:|---|
| `baseline_k127` | V_CAL_K=1.27 (committed) | "low" (post-overnight) | 19 | 1.0145 | 2.8666 | +182.6 | K=1.27 catastrophically overshoots at this position |
| `iter1_k041` | V_CAL_K=0.41 | same low | 19 | 1.0256 | 0.7432 | −27.5 | Over-correction the other way |
| `iter2_k0566` | V_CAL_K=0.566 | same low | 18 | 0.9441 | 0.9577 | **+1.44** | Position-fit K within ±5 % |
| `iter2_confirm` | V_CAL_K=0.566 | same low | 18 | 0.9485 | 0.9826 | **+3.60** | Confirmation of iter2 |
| `iter3_repos_k0566` | V_CAL_K=0.566 | "new" remount | n/a | n/a | n/a | n/a | Device hung, recovered by reflash |
| `iter3_repos_k0283` | V_CAL_K=0.283 | new remount | 16 | 0.8278 | 0.5556 | −32.9 | K=0.566 was too high at new pos |
| `iter5_bot_core_only` | dual-threshold BOT-core, K=1.0 | low | 14 | 0.7526 | 0.7617 | **+1.21** | New algorithm passes at this position |
| `iter5_pos2` | dual-threshold BOT-core | high (V_50_05-era reposition) | 0 | 0.7656 | 0.0 | −100 | Stale thresholds, drops not detected — device needed reset |
| `iter5b_top_low_highpos` | TOP-low only, K=1.0 | high splash | 9 | 0.7092 | 0.3580 | −49.5 | TOP under-saturated + missed drops |
| `iter5b_pos3_top_low` | TOP-low only, K=1.0 | mid-low remount | 14 | 0.7178 | 1.2225 | +70.3 | Umbilical inflated TOP_low at this pos |
| `iter7_hybrid_pos3` | hybrid (BOT_core / splash→TOP_low) | mid-low | 13 | 0.6757 | 0.5229 | −22.6 | Stable per-drop CV but biased low |
| `iter7b_stable` | hybrid (no adaptive) | mid-low | 11 | 0.6787 | 0.4480 | −34.0 | Drip rate slowed → drops grew to ~62 µL |

Each run is `<tag>_summary.txt` (run-level numbers), `<tag>_uart.log` (raw UART stream incl. `DROP,…` rows and per-drop `EVT,…,PULSES,…` diagnostics), and `<tag>_scale.csv` (Mettler-Toledo SIR stream at ~23 Hz).

The afternoon mount position was **not** the same as the V_50_01..05 morning campaign — the device sat lower on the chamber, drops hadn't fully detached at the TOP beam (umbilical visible in extended pulse_TOP_low), and the BOT beam was further from the pool (so splash was less dominant at the new "low" position but reappeared at the V_50_05-era remount). Drip rate also slowed over the afternoon (from ~50 mL/h to ~40 mL/h), so per-drop true volume drifted from 53.8 µL to 62 µL by Tate's-Law surface-tension dependence. Methodology was deliberately exploratory — see `docs/limitations.md` §Position-dependence for the interpretation.
