# Testing and Validation — Dripito Rev-B

Pre-registered validation protocol. This document is committed **before** any
official data collection (see commit history for the registration timestamp)
and is the bench-side reference for every experiment from first power-on
through the final validation dataset. Each entry states what is needed
physically, what firmware state is required, what the output looks like, and
why it is being run.

**Validation window:** 2026-05-07 → 2026-05-10 (compressed from original
2026-05-05 → 2026-05-10 due to enclosure schedule slip; compression
acknowledged in `docs/limitations.md`).
**Drip set available:** Macro 20 gtt/mL (only) — see EXP-3 limitation note.
**Ground truth method:** Gravimetric (precision scale ±0.0001 g).
**Secondary ground truth:** 240 fps phone video (hand-count cross-check).

Dataset, calibration logs, and analysis notebook are deposited on Zenodo with
DOI: *(populated at submission)*.

---

## EXP-0 — Optical Threshold Calibration

**Date:** 2026-05-07 morning (one-time bench cal — lab is light-controlled,
no daily recal needed).
**Duration:** ~1 hour.
**Firmware approach:** see `docs/decisions/auto-calibration-at-boot.md`
(forthcoming) — manual `#define` thresholds primary, optional auto-cal at
boot as enhancement.

### What you need

- Board 1 with IR LEDs and photodiodes soldered (TOP and BOT positions)
- Board 1 mounted in the printed enclosure
- **Real drip chamber + IV bag with saline/water**, gravity-fed at the head
  height EXP-3 will use — drip chamber is the actual deployment optical
  context, not a syringe stand-in
- Laptop with serial terminal (115200 baud, e.g. PuTTY or CoolTerm)
- STLink connected
- *Optional:* oscilloscope for an initial visual sanity check on waveform
  shape (10-min confidence builder; not the data source — UART → CSV is the
  reproducible path)

### Firmware required

Dashboard loop already streams UART. Temporarily add a CSV line that emits
raw ADC values continuously:

```
RAW,<top_raw>,<bot_raw>,<HAL_GetTick()>
```

The baseline (no drop) and the dip during a drop must be observed before a
threshold can be set.

### Primary path: manual `#define` thresholds (the path that ships)

1. Power on, open serial terminal, let it stabilise for 10 s.
2. Record 20–30 lines of baseline (no drop passing). Compute mean and range
   for `top_raw` and `bot_raw`.
3. Open the IV-bag roller clamp slowly so drops fall through the drip
   chamber at ~30 drops/min.
4. Capture ~30 s of UART output as drops pass. Find the minimum `top_raw`
   during a drop passage and the minimum `bot_raw`.
5. Set `THRESH_TOP = (baseline_top_mean + min_during_drop_top) / 2`. Repeat
   for BOT.
6. Hard-code these as `#define` in `main.h`. Rebuild + flash.
7. **Verification gate — 20+ drops, zero false positives.** Open the roller
   clamp and confirm every drop triggers detection. Then close the clamp;
   run 60 s with zero drops passing the sensor and count any false
   triggers. Acceptable: 0 false triggers in 60 s. If >0, lower the
   threshold or investigate alignment before proceeding.
8. **Log the calibration result** — append a row to
   `data/calibration_log.csv`:

```
date,board_id,mode,thresh_top,thresh_bot,baseline_top_mean,baseline_bot_mean,false_pos_60s,notes
2026-05-07,board1,manual,2400,2350,3105,3092,0,initial bench calibration
```

### Optional enhancement: auto-calibration at boot

If firmware time permits before 2026-05-07, the device may auto-calibrate at
boot by sweeping LEDs and computing thresholds dynamically. Architecture and
rationale: `docs/decisions/auto-calibration-at-boot.md` (forthcoming).
**Manual `#define` values remain the safety net** — if auto-cal fails its
sanity check or is not implemented, the manual path is the validated path.

If auto-cal is enabled, the firmware streams its result over UART as:

```
CAL,top_baseline,bot_baseline,top_thresh,bot_thresh,ms_since_boot
```

Capture each boot's CAL line and append to `calibration_log.csv` with
`mode=auto`. The verification gate (step 7 above) still applies regardless
of mode.

### Expected output (RAW stream)

```
RAW,3102,3089,1200
RAW,3098,3091,1400
RAW,1843,3088,1600   ← drop passing TOP beam
RAW,3101,1791,1650   ← drop passing BOT beam
RAW,3104,3092,1800
```

Absolute baseline + dip values are not yet known — Rev-B detection hardware
differs from Rev-A and has not been characterised. The shape (stable
baseline → sharp dip per drop → return to baseline) is what matters for
setting threshold. If dip magnitude is shallow (<300 counts) or noisy, the
optical alignment is off — fix before proceeding.

### Repo figures produced from this experiment

Two figures fall out of the calibration data, both committed to
`analysis/figures/`:

1. **Calibration sweep profile** (`fig_calibration_sweep.png`). X-axis:
   sample index. Y-axis: ADC value. TOP and BOT channels in two colors.
   Overlay horizontal lines at baseline mean and chosen threshold. Annotate
   one drop event with arrows for "baseline," "minimum," "threshold." Goes
   in README under "Detection Architecture."
2. **Calibration log table / plot** (`fig_calibration_log.png` or markdown
   table). Per-board-per-session threshold values from
   `calibration_log.csv`. With single-session calibration this is a one-row
   reference table; if auto-cal is enabled, multiple boot rows demonstrate
   stability across power cycles.

Plotting code lives in `analysis/notebooks/calibration.ipynb`, sourced from
`data/calibration_log.csv` and the captured RAW stream.

### Why

**Gate experiment.** Nothing downstream is valid if the thresholds are
wrong. False positives (ambient noise triggering detection) corrupt every
CSV. False negatives (drops not detected) give systematically low flow
rates. The verification gate (20+ drops, zero false positives in 60 s) is a
measurable quality criterion, not a vibe.

---

## EXP-1 — Enclosure Geometry Measurement

**Date:** 2026-05-07 morning (while EXP-0 firmware compiles).
**Duration:** ~30–45 minutes (depending on number of assembled units).

### What you need

- Every assembled Rev-B unit (sensor arm printed, optics installed)
- Digital calipers (±0.05 mm resolution)
- Ruler and phone camera

### Firmware required

None — this is a physical measurement.

### Procedure

1. Measure **d** (centre-to-centre distance between TOP and BOT beam axes
   along the drip path) on **every assembled board**. Measure each board
   three times at the same reference position, take the mean per board.
2. Compute: mean `d` across all assembled boards + standard deviation. The
   SD quantifies manufacturing variability from FDM print tolerances.
3. Compare measured mean to nominal CAD value. Flag any systematic offset
   (e.g. shrinkage in print direction).
4. Photograph the sensor arm with a ruler in frame (figure for the repo).
5. Record in `data/geometry.json`:

```json
{
  "beam_separation_mm":        {"mean": 14.2, "sd": 0.3, "n_boards_measured": 5, "cad_nominal_mm": 14.0},
  "caliper_resolution_mm":     0.05,
  "positioning_uncertainty_mm": 0.5,
  "measured_by":               "digital calipers",
  "measurement_date":          "2026-05-07",
  "notes": "positioning uncertainty estimated from repeated placement; dominates over caliper resolution"
}
```

### Uncertainty note

Caliper resolution is ±0.05 mm, but physical positioning of the caliper jaw
against the beam axis adds approximately ±0.5 mm. This positioning
uncertainty dominates. A 1 mm error in `d` propagates **cubically to
volume** (sphere model: V ∝ d³). This is the single largest source of
systematic error in the calibration model and must be reported in the
Discussion.

### Expected output

`d` will likely be 8–20 mm depending on sensor arm design. Board-to-board
SD should be < 1 mm for a well-printed enclosure; if SD > 1 mm, print
tolerance is a named limitation.

### Why

The dual-beam velocity model is `velocity = d / transit_time`. A 1 mm
error in `d` propagates linearly to velocity, then linearly to diameter,
then **cubically to volume**. Measuring `d` on all 5 units rather than one
anchors the uncertainty budget quantitatively and demonstrates systematic
experimental thinking.

---

## EXP-2 — Firmware Shakeout Runs (Informal)

**Date:** 2026-05-07 afternoon.
**Duration:** ~2 hours.

### What you need

- Full bench setup: IV stand, Ringer's lactate or saline bag (500 mL), macro
  20 gtt/mL drip set, collection container on the scale
- Board 1 in enclosure, STLink connected, laptop logging CSV
- EXP-0 thresholds set, EXP-1 geometry recorded

### Firmware required

Full dual-beam detection active:

- TIM3 free-running µs counter
- Edge detection state machine (IDLE → TOP_ACTIVE → BOT_ACTIVE → COMPLETE)
- UART CSV per drop:
  `abs_ms,drop_N,transit_us,pulse_top_us,pulse_bot_us,top_raw,bot_raw`
- Flow rate computed and displayed on LCD line 2

### Procedure

1. Set IV bag at measured head height (see EXP-3), clamp roller to achieve
   ~50 mL/hr visually.
2. Run 5 min, watch serial CSV. Save to
   `data/shakeout/YYYY-MM-DD_shakeout_01.csv` — not official data but saved
   for reference.
3. Check: are `transit_us` values consistent drop-to-drop? High variance
   (>50% CV) indicates beam misalignment or threshold instability — **do
   not proceed to EXP-3 until resolved.**
4. Check: does LCD flow rate converge after 5–6 drops to something close to
   the roller setting?
5. Run at 20 mL/hr and 100 mL/hr briefly. Verify detection still works at
   both extremes.
6. Fix any firmware issues found before starting the official campaign.

### Exit criteria for proceeding to EXP-3

- Zero false triggers in 60 s at each flow rate extreme (20 and 100 mL/hr)
- `transit_us` CV < 50% at 50 mL/hr over ≥20 consecutive drops
- LCD flow rate within ±30% of roller setting after 5-drop warm-up

If any criterion fails, log the failure in `data/shakeout/` and resolve
before official data.

### Why

These runs are **not** in the pre-registered dataset — they are debugging
runs. Running them separately protects the integrity of the official
campaign. Saving them to `data/shakeout/` rather than discarding provides
an audit trail. The exit criteria define a measurable quality gate rather
than a subjective judgement call.

---

## EXP-3 — Main Validation Campaign

**Date:** 2026-05-07 → 2026-05-08.
**Duration:** ~4 hours active collection, spread across the two days.

> **⚠ Scope limitation:** Only macro 20 gtt/mL drip sets are available. The
> original protocol planned 3 drip sets (macro 10, macro 20, micro 60).
> Micro 60 is the standard paediatric drip set — its omission limits the
> generalisability of results to adult/macro-set use cases. This limitation
> is explicitly acknowledged here and must be stated in the Discussion. It
> does not invalidate the validation; it scopes its conclusions.

### What you need

- Full bench setup (same as EXP-2)
- Precision scale (tare the collection container before each run)
- 240 fps phone camera mounted to capture the drip chamber
- Laptop logging UART CSV to named files
- Enough Ringer's lactate for ~2.5 hours of flow (500 mL bag per session)
- Roller clamp set to target flow rates using a reference table or online
  calculator
- Stopwatch (phone is fine)
- Tape measure (fix head height at a measured value — see setup below)
- Thermometer + note ambient light condition per session

### Setup (fixed once, recorded once)

- **Head height:** Measure IV bag bottom to drip chamber top with tape
  measure. Fix this distance at a specific value (e.g. 95 cm) and record it
  in `data/session_log.csv`. Do not change it between runs.
- **Board under test:** Record board ID in every CSV filename (e.g.
  `board1`). Use the same board for all EXP-3 runs unless a hardware
  failure forces a swap (log any swap).

### Environmental logging

At the start of each session, append a row to `data/session_log.csv`:

```
date,board_id,head_height_cm,room_temp_c,light_condition,notes
2026-05-07,board1,95,21,indoor_fluorescent_blinds_closed,
```

### Flow stabilisation criterion

Before starting the 5-minute timer: count 10 consecutive drops and confirm
the inter-drop interval is consistent (±15% of the mean). If not stable
after 90 s, log the delay and wait.

### Run matrix

| Run ID | Flow Rate | Drip Set | Trials | Notes |
|--------|-----------|----------|--------|-------|
| V_20_01 – V_20_05 | 20 mL/hr | Macro 20 | 5 | Low-flow, surface tension dominant |
| V_50_01 – V_50_05 | 50 mL/hr | Macro 20 | 5 | Mid-range clinical |
| V_100_01 – V_100_05 | 100 mL/hr | Macro 20 | 5 | High-flow, smaller drops |

**Total: 15 official runs.**

### Per-run procedure

1. Tare scale with empty container.
2. Set roller clamp to target flow rate. Wait for stabilisation criterion
   (above).
3. Start stopwatch + phone camera.
4. Open new CSV log file named
   `YYYY-MM-DD_macro20_XXmlh_trialN_board1.csv`.
5. Collect for exactly **5 minutes**.
6. Stop CSV logging, stop camera, weigh collection container.
7. Record: `gravimetric_mass_g`, `run_duration_s`, `drop_count_device`, CSV
   filename, ambient notes.
8. Compute:
   `gravimetric_flow_mlh = (mass_g / 1.005) / (duration_s / 3600)`
   (density of Ringer's lactate: 1.005 g/mL — Lacy et al., *Drug
   Information Handbook*, 2009).

### Pre-registered discard rule

A run is discarded and repeated if:

- Tubing kinked or flow visibly disrupted mid-run
- Scale reading shows clearly incorrect mass (e.g. container shifted)
- CSV shows >5 s gap in drop events without roller adjustment (firmware
  crash or alignment loss)
- Flow stabilisation criterion was not met before the timer started and
  this was not logged

Discard reason must be logged in `data/session_log.csv`. This rule was
defined before data collection (pre-registered).

### Expected CSV output (one run)

```
abs_ms,drop_N,transit_us,pulse_top_us,pulse_bot_us,top_raw,bot_raw
3200,1,29800,17600,17200,1821,1795
12100,2,30100,17900,17500,1838,1810
...
```

At 50 mL/hr with macro 20: ~16.7 drops/min → ~83 drops in 5 min. At 20
mL/hr: ~33 drops. At 100 mL/hr: ~167 drops.

### Why

This is the core evidence for the project. The Bland-Altman analysis in
EXP-6 is built entirely from these 15 runs. Five trials per flow rate
compensates for having a single drip-set type by increasing statistical
power within the available scope. The three flow rates cover the
clinically relevant range (10–125 mL/hr per IEC 60601-2-24).

---

## EXP-4 — Rev-A Baseline (Prior-Art Comparison)

**Date:** 2026-05-08 (interleave with EXP-3).
**Duration:** ~1.5 hours.

### What you need

- Board running **InfusionBA (Rev-A firmware)** — the legacy STM32G030
  project at `firmware/STM32CubeIDE/InfusionBA/`
- Same bench setup as EXP-3, identical head height and conditions
- Same scale and logging procedure

### Firmware required

Rev-A firmware (InfusionBA project, not InfusionBA2). Flash to a spare
board or swap firmware. **Record the exact git commit hash of the Rev-A
firmware used** — paste it into `data/session_log.csv` for the Rev-A
session. Without a commit hash, the baseline is not reproducible.

**Rev-A fixed drip factor:** InfusionBA uses a hard-coded drip-to-volume
conversion assuming 20 gtt/mL (verify in `main.c` before running). Since
EXP-4 also uses macro 20, this factor matches — note it explicitly. At
different drip-set sizes, Rev-A accuracy would degrade further; this is a
named Rev-A limitation.

### Run matrix

| Run ID | Flow Rate | Drip Set | Trials |
|--------|-----------|----------|--------|
| A_20_01 – A_20_03 | 20 mL/hr | Macro 20 | 3 |
| A_50_01 – A_50_03 | 50 mL/hr | Macro 20 | 3 |
| A_100_01 – A_100_03 | 100 mL/hr | Macro 20 | 3 |

**Total: 9 runs.** Three trials per flow rate gives a Rev-A MAPE with
uncertainty, making the Rev-B vs Rev-A comparison statistically meaningful.

### Expected output

Rev-A outputs a single flow-rate number (drops/min × fixed drip-factor ×
conversion). Compare to gravimetric truth. Expected to show larger error at
low flow rates where drop volume varies with surface tension regime. If
Rev-B does not outperform Rev-A at all flow rates, report this honestly —
it is still valid data.

### Why

Without a measured Rev-A baseline, any claim that "Rev-B is more accurate"
is architectural argument. Nine runs of Rev-A under identical conditions
gives a quantitative comparison: Rev-B MAPE ± CI vs Rev-A MAPE ± CI at each
flow rate.

---

## EXP-5 — Edge-Case Stress Tests

**Date:** 2026-05-08 (after main campaign complete).
**Duration:** ~1.5 hours.

### What you need

- Same full bench setup
- Small syringe (to inject an air bubble upstream)
- Extra IV bag (near-empty simulation)
- Bright desk lamp (ambient light interference test)
- Stopwatch

### Firmware required

Same as EXP-3. No changes — the point is to probe the firmware's
robustness as-is.

### Pre-defined output format

For each test, record in `data/edge_cases/EC_XX_YYYY-MM-DD.md`:

```
Scenario | False events in 60 s | Observed LCD behaviour | Root cause hypothesis | Proposed Rev-C mitigation
```

This format is defined here (pre-registered) so the Discussion section is
not shaped post-hoc by what happened.

### Test matrix

| Test ID | Scenario | Method | What to look for |
|---------|----------|--------|-----------------|
| EC-01 | Air bubble | Inject ~3 mL air via syringe into an upstream port; note approximate bubble length in tubing | Does firmware generate a false drop event? Does flow rate spike? |
| EC-02 | Near-empty bag | Let bag drain to <50 mL remaining (reduced head pressure → lower flow) | Does flow rate track the gradual change, or report stale values? |
| EC-03 | Ambient light | Point a 60W-equivalent desk lamp at the sensor arm from **30 cm distance** | Does baseline ADC shift enough to cause false triggers? Count false events in 60 s. |
| EC-04 | Tubing micro-vibration | Tap the IV pole firmly 3 times mid-run | Does mechanical vibration produce ghost drops? |
| EC-05 | Gradual head pressure drop | Lower bag from 95 cm to 50 cm mid-run (simulate bag running dry) | Does the device track the flow-rate decrease, or lag / alarm incorrectly? |

EC-05 is the most clinically relevant: a bag running low is the primary
scenario the device is designed to detect.

### Expected output

Edge cases are expected to produce some errors. The output is a filled
table (using the pre-defined format above) in `data/edge_cases/`. These
tables feed directly into the Discussion section of the README.

### Why

Edge-case runs are Discussion gold. A bubble causing a false detection
motivates a future minimum-pulse-width filter. Ambient light shifting the
baseline motivates adaptive thresholding in Rev-C. Anticipating failure
modes and documenting them honestly produces a stronger Discussion
section than only reporting successes.

---

## EXP-6 — Analysis Pipeline (Post-Collection)

**Date:** 2026-05-09 → 2026-05-10.
**Location:** `analysis/` in this repository (Jupyter notebook).

### Inputs

- All 15 official CSVs from EXP-3
- 9 Rev-A CSVs from EXP-4
- `data/geometry.json` from EXP-1
- `data/calibration_log.csv` from EXP-0
- `data/session_log.csv`
- Gravimetric log spreadsheet

### Step 1: Calibration model fit

**Assumption (stated explicitly):** Drops are modelled as spheres. This is
a simplifying assumption — real drops deviate from spherical geometry,
particularly at low flow rates where surface tension prolongs the
detachment phase. The scalar correction factor `k` (step below) partially
absorbs this deviation.

From each drop event, compute estimated drop volume:

```
velocity_m_s     = d_m / (transit_us × 1e-6)
diameter_m       = pulse_top_us × 1e-6 × velocity_m_s
volume_nL        = (π / 6) × (diameter_m × 1e9)³
```

**Train/test split:** Use 10 runs (randomly selected, stratified by flow
rate: 3–4 per rate) to fit the scalar correction factor `k` by
least-squares against gravimetric truth. Apply the fitted `k` to the
remaining 5 runs and report out-of-sample MAPE separately from in-sample
MAPE. Report both. If in-sample MAPE is substantially lower than
out-of-sample, note this as evidence of overfitting to the small dataset.

`k` absorbs beam-width bias and sphere-model deviation. Report `k` and its
physical interpretation.

### Step 2: Bland-Altman analysis

**The Bland-Altman plot is the primary deliverable of the entire
validation campaign.** It is the international standard for comparing two
measurement methods (Bland & Altman, *Lancet*, 1986) and is required by
IEC 60601-2-24 convention for infusion device validation.

- X-axis: mean of device reading and gravimetric reading (mL/hr)
- Y-axis: difference between device reading and gravimetric reading
  (mL/hr)
- Lines: mean bias ± 1.96 × SD = **95% Limits of Agreement (LoA)**

**Acceptable range for a medical IV monitor (IEC 60601-2-24 §51.105):**
mean bias < ±2 mL/hr; 95% LoA within ±15% of mean flow rate or ±5 mL/hr,
whichever is wider.

Generate: one plot per flow rate (20, 50, 100 mL/hr) + one combined.
Per-flow-rate plots reveal whether accuracy degrades at low flow rates
(expected finding for surface-tension-limited drop formation).

### Step 3: MAPE table with 95% confidence intervals

Report bootstrap 95% CI on each MAPE value (resample runs with
replacement, n = 10,000 iterations — trivial in Python with
`np.random.choice`).

| Flow Rate | Rev-B MAPE (95% CI) | Rev-A MAPE (95% CI) | N runs (Rev-B / Rev-A) |
|-----------|---------------------|---------------------|------------------------|
| 20 mL/hr  | ? (?, ?)            | ? (?, ?)            | 5 / 3                  |
| 50 mL/hr  | ? (?, ?)            | ? (?, ?)            | 5 / 3                  |
| 100 mL/hr | ? (?, ?)            | ? (?, ?)            | 5 / 3                  |

### Step 4: Error vs. flow rate plot

Scatter: x = flow rate, y = % error per run. Trend line. If error
increases at low flow rates, this confirms the surface-tension regime
hypothesis.

### Step 5: Drop volume distribution per flow rate

Box plots of `volume_nL` per drop at each flow rate. Expected: drop volume
decreases at higher flow rates. This is the mechanistic validation of the
calibration model.

### Why Bland-Altman and not R²

R² measures correlation, not agreement. Two methods can be strongly
correlated yet systematically differ by a fixed offset. Bland-Altman
shows both bias and spread. For a medical device being compared to a
reference standard, R² is insufficient and its use would signal
unfamiliarity with medical device validation methodology.

---

## Quick-reference timeline

```
May 05 (today)   Repo restructure + protocol commit (this document)
May 06           Full work day — no Dripito time
May 07           EXP-0 (cal) | EXP-1 (geometry) | EXP-2 (shakeout) | EXP-3 V_20_01–05 + V_50_01–03
May 08           EXP-3 V_50_04–05 + V_100_01–05 | EXP-4 Rev-A (9 runs) | EXP-5 edge cases
May 09           EXP-6 analysis: calibration fit + Bland-Altman + MAPE + plots
May 10           Notebook clean + committed | session_log final | Zenodo dataset deposit
May 11–13        Repo sprint: README, docs/, CI, tag v1.0-submission
```

---

## Pre-run checklist (laminate and put on bench)

- [ ] EXP-0 recalibration done this session, result logged in
      `data/calibration_log.csv`
- [ ] Bag hanging at fixed, measured head height (record in
      `data/session_log.csv`)
- [ ] Room temperature and light condition noted in `data/session_log.csv`
- [ ] Collection container tared on scale
- [ ] UART logging active (correct COM port, 115200 baud)
- [ ] Log file named correctly:
      `YYYY-MM-DD_macro20_XXmlh_trialN_board1.csv`
- [ ] Camera recording at 240 fps, aimed at drip chamber window
- [ ] Flow stabilised: 10 consecutive drops with inter-drop interval
      CV < 15%
- [ ] Stopwatch ready to mark exact 5:00 collection window
- [ ] Ambient conditions noted
