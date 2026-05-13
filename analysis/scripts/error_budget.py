"""A priori Monte Carlo error budget for dual-beam drop-volume measurement.

Predicts MAPE and Bland-Altman LoA BEFORE bench data exists, by
propagating measurement uncertainty through the firmware's volume-
inversion math. Run this, commit the predicted figure, THEN take
bench data — the timestamped sequence is what turns the prediction
into a defensible claim rather than post-hoc fitting.

Method
------
1. Sample run-level latent state: per-run beam-separation drift
   (alignment + caliper) drawn ONCE per ~30-drop run and held
   constant across that run's drops. This is the dominant source
   for d=10 mm and produces hierarchical structure visible in
   per-drop Bland-Altman: tight within-run clusters, wide
   between-run scatter.
2. Sample drop-level latent: true drop volume (drip-set CV) and
   drop velocity.
3. Add per-drop measurement noise: ADC sampling discretisation,
   threshold-crossing jitter.
4. Invert with the firmware's formula, using *nominal* `d` — the
   firmware never knows the actual per-run separation, which is
   exactly why alignment becomes a measurement error.
5. Compare device estimate to latent truth → one Bland-Altman
   point per drop.
6. Ablation: zero each noise source in turn, recompute MAPE, and
   attribute the delta to that source.

Volume-inversion math (firmware view)
-------------------------------------
For each drop, the firmware sees two timing intervals:

  transit_us    = time between TOP-beam and BOT-beam crossings
                  = d_actual / v_drop
  dip_duration_us = time TOP beam stays blocked
                  ≈ D_drop / v_drop

Their ratio cancels v_drop:

  D_est = d_nominal * (dip_duration_us / transit_us)
  V_est = (pi/6) * D_est**3

So the volume estimate depends on `d` and on a TIMING RATIO, not
on absolute velocity. Velocity uncertainty enters only through how
relative the timing jitter is.

Pre-bench prediction at d=10 mm (with default params)
-----------------------------------------------------
- alignment ±2 mm rectangular → 1-sigma 1.155 mm → 11.5% relative
  on d → ~35% on volume (cubic) within a run, scrambled across runs
- caliper d_sd  0.05 mm → 0.5% relative on d → small
- timing jitter 20 µs on ~12500 µs transit → 0.16% on ratio
- ADC discretisation 100 µs → 0.4% on transit, 0.9% on dip
- drop volume CV 8% (drip-set inherent)

Alignment is predicted to dominate. The bench either confirms or
overturns that — both are useful answers.

Parameters needing later refinement
-----------------------------------
- d_sd_mm: replace placeholder with EXP-1 caliper SD (n=5 repeats)
- adc_sample_period_us: read from firmware
- threshold_jitter_us: from firmware design
- drop_volume_cv: post-bench, fit from per-run gravimetric data

Re-running with refined params re-generates the figure; the
ORIGINAL committed figure is the pre-bench prediction.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Default RNG seed = bench date (2026-05-13). Fixed so re-runs are byte-identical.
DEFAULT_SEED = 20260513

# Defaults match the bench plan in Repo 6.0 Playbook (Active/...2026-05-12.md).
DEFAULT_RATES_MLH: tuple[float, ...] = (20.0, 50.0, 100.0)
DEFAULT_DROPS_PER_RUN = 30
DEFAULT_RUNS_PER_RATE = 5
DEFAULT_MC_CAMPAIGNS = 1000

# Ablation can use fewer campaigns since we only need pooled MAPE.
DEFAULT_ABLATION_CAMPAIGNS = 400


@dataclass(frozen=True)
class NoiseModel:
    """Every input that feeds the volume estimate, with its uncertainty.

    Field-level documentation is the assumption table — every value
    must trace to a measurement, a datasheet, or a flagged placeholder.
    """

    # --- Geometry ---
    d_mean_mm: float            # CAD spec: TOP-BOT beam separation (centre-to-centre)
    d_sd_mm: float              # Caliper repeatability SD (5 repeats on board 1)
    alignment_sd_mm: float      # Per-run chamber-mount drift, 1-sigma

    # --- Drop hydraulics ---
    drop_volume_mean_ul: float  # Macro 20 gtt/mL nominal = 50 µL
    drop_volume_cv: float       # Drop-to-drop variability (surface-tension regime)
    drop_velocity_mean_ms: float  # Mean drop velocity at the sensor arm
    drop_velocity_cv: float     # Drop-to-drop velocity CV (small at fixed head height)

    # --- Optical / timing ---
    adc_sample_period_us: float  # Firmware ADC sample period (discretises timing)
    threshold_jitter_us: float   # 1-sigma threshold-crossing detection jitter


def default_params() -> NoiseModel:
    """Best-estimate defaults as of 2026-05-13 (pre-bench).

    Parameter sources
    -----------------
    - d_mean_mm:            CAD spec, confirmed 2026-05-13
    - d_sd_mm:              Bambu Lab 3D-print tolerance ±0.2 mm rectangular
                            → 0.2/sqrt(3) ≈ 0.115 mm. The TOP-BOT beam pitch
                            is set by the printed sensor arm geometry, not
                            by chamber mount, so this is a one-shot
                            print-quality term.
    - alignment_sd_mm:      ZERO. The drip chamber can wiggle vertically
                            inside the casing (which affects v_drop, not d)
                            but cannot change the printed beam pitch. The
                            ±2 mm rectangular estimate in the Repo 6.0
                            Playbook was a pessimism that the print
                            geometry rules out.
    - drop_volume_mean_ul:  macro 20 gtt/mL → 1000/20 = 50 µL
    - drop_volume_cv:       PLACEHOLDER 8% (literature range 5-10%);
                            refine post-bench from per-drop gravimetric.
    - drop_velocity_mean_ms: free-fall v = sqrt(2 g h) with h ≈ 30 mm
                            (orifice → TOP beam) → ~0.77 m/s
    - drop_velocity_cv:     0.08 to absorb run-to-run chamber-mount height
                            variability (chamber wiggle moves the fall
                            distance ± a few mm)
    - adc_sample_period_us: PLACEHOLDER; verify against firmware ADC config
    - threshold_jitter_us:  PLACEHOLDER; verify against firmware design
    """
    return NoiseModel(
        d_mean_mm=10.0,
        d_sd_mm=0.2 / np.sqrt(3.0),
        alignment_sd_mm=0.0,
        drop_volume_mean_ul=50.0,
        drop_volume_cv=0.08,
        drop_velocity_mean_ms=0.77,
        drop_velocity_cv=0.08,
        adc_sample_period_us=100.0,
        threshold_jitter_us=20.0,
    )


# Field names of NoiseModel that can be ablated (zeroed) one at a time.
#
# Label notes:
#   "Print tolerance (3D)" — d_sd_mm models the per-board variability of the
#     printed sensor-arm beam pitch from the nominal CAD value. The firmware
#     uses d_nominal in its inversion, so per-board geometric scatter creates
#     a baked-in systematic bias. "Caliper repeatability" would be the residual
#     uncertainty AFTER per-unit calibration; today no per-unit cal is done.
#   "Drop volume CV" / "Drop velocity CV" — these are properties of the drip
#     set's drops themselves, not of the device. They contribute ~0 to MAPE
#     because the firmware's (dip/transit) ratio is velocity-invariant and
#     measures whatever volume actually formed.
#   "Alignment drift (per-run)" — would matter if d changed between runs.
#     Zero here because the printed arm fixes d rigidly across remounts.
_ABLATABLE_SOURCES: tuple[tuple[str, str], ...] = (
    ("alignment_sd_mm", "Alignment drift (per-run)"),
    ("d_sd_mm", "Print tolerance (3D)"),
    ("drop_volume_cv", "Drop volume CV"),
    ("drop_velocity_cv", "Drop velocity CV"),
    ("threshold_jitter_us", "Timing jitter"),
    ("adc_sample_period_us", "ADC discretisation"),
)


def _diameter_from_volume_mm(volume_ul: np.ndarray) -> np.ndarray:
    """Sphere model: D = (6V/pi)^(1/3). V in µL = mm³, returns mm."""
    return np.cbrt(6.0 * volume_ul / np.pi)


def _volume_from_diameter_ul(diameter_mm: np.ndarray) -> np.ndarray:
    return (np.pi / 6.0) * np.power(diameter_mm, 3)


def simulate(
    params: NoiseModel,
    rates_mlh: Iterable[float] = DEFAULT_RATES_MLH,
    n_campaigns: int = DEFAULT_MC_CAMPAIGNS,
    runs_per_rate: int = DEFAULT_RUNS_PER_RATE,
    drops_per_run: int = DEFAULT_DROPS_PER_RUN,
    seed: int = DEFAULT_SEED,
    zero_terms: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Run the Monte Carlo, fully vectorised.

    Parameters
    ----------
    params         : NoiseModel
    rates_mlh      : flow rates to sweep (mL/hr; affects layout only,
                     not per-drop physics in this model)
    n_campaigns    : number of synthetic 5-run-per-rate campaigns
    runs_per_rate  : runs per flow rate per campaign
    drops_per_run  : drops per simulated run
    seed           : RNG seed
    zero_terms     : NoiseModel field names to force to zero
                     (used by ablation; () = full model)

    Returns
    -------
    Long-form DataFrame, one row per simulated drop:
      campaign_id, run_id, flow_rate_target_mlh, drop_idx,
      v_true_ul, v_est_ul, d_actual_mm
    """
    rng = np.random.default_rng(seed)
    rates = np.asarray(list(rates_mlh), dtype=float)
    n_rates = len(rates)

    n_runs = n_campaigns * n_rates * runs_per_rate
    n_drops = n_runs * drops_per_run

    align_sd = 0.0 if "alignment_sd_mm" in zero_terms else params.alignment_sd_mm
    d_sd = 0.0 if "d_sd_mm" in zero_terms else params.d_sd_mm
    vol_cv = 0.0 if "drop_volume_cv" in zero_terms else params.drop_volume_cv
    vel_cv = 0.0 if "drop_velocity_cv" in zero_terms else params.drop_velocity_cv
    jitter = 0.0 if "threshold_jitter_us" in zero_terms else params.threshold_jitter_us
    period = 0.0 if "adc_sample_period_us" in zero_terms else params.adc_sample_period_us

    # --- Per-run latent state: alignment + caliper, sampled ONCE per run ---
    d_run_sd = float(np.sqrt(align_sd**2 + d_sd**2))
    if d_run_sd > 0:
        d_actual_per_run = params.d_mean_mm + rng.normal(0.0, d_run_sd, size=n_runs)
    else:
        d_actual_per_run = np.full(n_runs, params.d_mean_mm)
    d_actual_per_drop = np.repeat(d_actual_per_run, drops_per_run)

    # --- Per-drop latent state ---
    v_true = rng.normal(params.drop_volume_mean_ul,
                        params.drop_volume_mean_ul * vol_cv,
                        size=n_drops)
    # Clip to avoid pathological negative volumes from the tails.
    v_true = np.clip(v_true, 1.0, None)
    d_true_mm = _diameter_from_volume_mm(v_true)
    v_drop = np.clip(rng.normal(params.drop_velocity_mean_ms,
                                params.drop_velocity_mean_ms * vel_cv,
                                size=n_drops),
                     0.01, None)
    # Convert m/s → mm/µs (1 m/s = 1e-3 mm/µs)
    v_drop_mm_us = v_drop * 1e-3

    # --- Physics: true timing intervals ---
    transit_true_us = d_actual_per_drop / v_drop_mm_us
    dip_true_us = d_true_mm / v_drop_mm_us

    # --- Measurement: add jitter, then ADC discretisation ---
    if jitter > 0:
        transit_meas = transit_true_us + rng.normal(0.0, jitter, n_drops)
        dip_meas = dip_true_us + rng.normal(0.0, jitter, n_drops)
    else:
        transit_meas = transit_true_us.copy()
        dip_meas = dip_true_us.copy()
    if period > 0:
        transit_meas = np.round(transit_meas / period) * period
        dip_meas = np.round(dip_meas / period) * period
    # Guard against zero/negative transit
    transit_meas = np.clip(transit_meas, max(period, 1.0), None)

    # --- Firmware inversion (uses NOMINAL d, not d_actual) ---
    d_est_mm = params.d_mean_mm * (dip_meas / transit_meas)
    v_est_ul = _volume_from_diameter_ul(d_est_mm)

    # --- Layout indices ---
    rate_per_run = np.tile(np.repeat(rates, runs_per_rate), n_campaigns)
    campaign_per_run = np.repeat(np.arange(n_campaigns), n_rates * runs_per_rate)
    rate_per_drop = np.repeat(rate_per_run, drops_per_run)
    campaign_per_drop = np.repeat(campaign_per_run, drops_per_run)
    run_idx_per_drop = np.repeat(np.arange(n_runs), drops_per_run)
    drop_idx_per_drop = np.tile(np.arange(drops_per_run), n_runs)

    return pd.DataFrame({
        "campaign_id": campaign_per_drop.astype(np.int32),
        "run_id": run_idx_per_drop.astype(np.int32),
        "flow_rate_target_mlh": rate_per_drop,
        "drop_idx": drop_idx_per_drop.astype(np.int16),
        "v_true_ul": v_true,
        "v_est_ul": v_est_ul,
        "d_actual_mm": d_actual_per_drop,
    })


def mape_pct(device: np.ndarray, truth: np.ndarray) -> float:
    return float(np.mean(np.abs((device - truth) / truth)) * 100.0)


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    """Per-rate predicted MAPE + bias + 95% LoA from drop-level DataFrame."""
    rows = []
    for rate, sub in df.groupby("flow_rate_target_mlh"):
        diff = sub["v_est_ul"].to_numpy() - sub["v_true_ul"].to_numpy()
        bias = float(np.mean(diff))
        sd = float(np.std(diff, ddof=1))
        rows.append({
            "rate_mlh": float(rate),
            "n_drops": int(len(sub)),
            "bias_ul": bias,
            "sd_ul": sd,
            "loa_lower_ul": bias - 1.96 * sd,
            "loa_upper_ul": bias + 1.96 * sd,
            "mape_pct": mape_pct(sub["v_est_ul"].to_numpy(), sub["v_true_ul"].to_numpy()),
        })
    return pd.DataFrame(rows).sort_values("rate_mlh").reset_index(drop=True)


def calibration_convergence(
    params: NoiseModel,
    rate_mlh: float = 50.0,
    n_drops_max: int = 30,
    n_bootstrap: int = 2000,
    cal_trim_lo: int = 1,
    cal_trim_hi: int = 1,
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    """Predict SD(V_cal) vs N_drops for the firmware's boot calibration.

    Scenario: one board calibrating against its OWN drops. The firmware's
    boot sequence collects N drops, sorts, trims `cal_trim_lo` from the
    low end and `cal_trim_hi` from the high end, averages the rest. The
    resulting V_cal becomes that session's locked drop-volume reference.

    Print tolerance (d_sd_mm) is zeroed for this analysis because the
    calibration is against THIS board's drops — the firmware doesn't
    care whether the absolute `d` is 9.9 or 10.1 mm, only that
    subsequent drops match V_cal. Within-board noise (drop CV, timing
    jitter, ADC discretisation) determines V_cal repeatability.

    Returns columns: n_drops, sd_v_cal_ul, sd_pct, mean_v_cal_ul.
    """
    p_within = NoiseModel(
        d_mean_mm=params.d_mean_mm,
        d_sd_mm=0.0,
        alignment_sd_mm=0.0,
        drop_volume_mean_ul=params.drop_volume_mean_ul,
        drop_volume_cv=params.drop_volume_cv,
        drop_velocity_mean_ms=params.drop_velocity_mean_ms,
        drop_velocity_cv=params.drop_velocity_cv,
        adc_sample_period_us=params.adc_sample_period_us,
        threshold_jitter_us=params.threshold_jitter_us,
    )
    df = simulate(p_within, rates_mlh=[rate_mlh], n_campaigns=n_bootstrap,
                  runs_per_rate=1, drops_per_run=n_drops_max, seed=seed)
    pivot = df.pivot(index="campaign_id", columns="drop_idx", values="v_est_ul")
    drops_array = pivot.to_numpy()
    rows = []
    for n in range(2, n_drops_max + 1):
        sub = drops_array[:, :n]
        if n >= cal_trim_lo + cal_trim_hi + 1:
            sorted_sub = np.sort(sub, axis=1)
            trimmed = sorted_sub[:, cal_trim_lo:n - cal_trim_hi]
        else:
            trimmed = sub
        means = trimmed.mean(axis=1)
        rows.append({
            "n_drops": n,
            "sd_v_cal_ul": float(np.std(means, ddof=1)),
            "mean_v_cal_ul": float(np.mean(means)),
            "sd_pct": float(np.std(means, ddof=1) / params.drop_volume_mean_ul * 100.0),
        })
    return pd.DataFrame(rows)


def ablation(
    params: NoiseModel,
    rates_mlh: Iterable[float] = DEFAULT_RATES_MLH,
    n_campaigns: int = DEFAULT_ABLATION_CAMPAIGNS,
    runs_per_rate: int = DEFAULT_RUNS_PER_RATE,
    drops_per_run: int = DEFAULT_DROPS_PER_RUN,
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    """Source-by-source ablation.

    For each ablatable field, force its SD to zero, re-run the MC,
    and record the resulting MAPE. Delta vs baseline = attributable
    contribution of that source.
    """
    rows = []
    df_base = simulate(params, rates_mlh, n_campaigns, runs_per_rate,
                       drops_per_run, seed, zero_terms=())
    base_pooled = mape_pct(df_base["v_est_ul"].to_numpy(),
                           df_base["v_true_ul"].to_numpy())
    base_by_rate = summarise(df_base).set_index("rate_mlh")["mape_pct"].to_dict()

    rows.append({"source": "Baseline (all noise)", "rate_mlh": "all",
                 "mape_pct": base_pooled, "delta_vs_baseline_pct": 0.0})
    for rate, mape_val in base_by_rate.items():
        rows.append({"source": "Baseline (all noise)", "rate_mlh": rate,
                     "mape_pct": mape_val, "delta_vs_baseline_pct": 0.0})

    for field, label in _ABLATABLE_SOURCES:
        df_abl = simulate(params, rates_mlh, n_campaigns, runs_per_rate,
                          drops_per_run, seed, zero_terms=(field,))
        abl_pooled = mape_pct(df_abl["v_est_ul"].to_numpy(),
                              df_abl["v_true_ul"].to_numpy())
        abl_by_rate = summarise(df_abl).set_index("rate_mlh")["mape_pct"].to_dict()
        rows.append({"source": label, "rate_mlh": "all",
                     "mape_pct": abl_pooled,
                     "delta_vs_baseline_pct": base_pooled - abl_pooled})
        for rate, mape_val in abl_by_rate.items():
            rows.append({"source": label, "rate_mlh": rate,
                         "mape_pct": mape_val,
                         "delta_vs_baseline_pct": base_by_rate[rate] - mape_val})
    return pd.DataFrame(rows)


def make_figure(
    df: pd.DataFrame,
    abl: pd.DataFrame,
    params: NoiseModel,
    title_suffix: str = "",
    convergence_df: pd.DataFrame | None = None,
) -> plt.Figure:
    """3-panel figure: ablation · predicted Bland-Altman · calibration convergence."""
    fig = plt.figure(figsize=(16, 5.2), dpi=130, constrained_layout=True)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.4, 1.1])

    # --- (a) Ablation waterfall: pooled-MAPE when each source is zeroed ---
    ax_a = fig.add_subplot(gs[0, 0])
    pooled = abl[abl["rate_mlh"] == "all"].copy().sort_values("mape_pct", ascending=True)
    # Move "Baseline" to the top by sorting it last on the axis.
    is_base = pooled["source"] == "Baseline (all noise)"
    pooled = pd.concat([pooled[~is_base], pooled[is_base]]).reset_index(drop=True)
    colors = plt.cm.YlOrRd(np.linspace(0.30, 0.85, len(pooled)))
    bars = ax_a.barh(pooled["source"], pooled["mape_pct"],
                     color=colors, edgecolor="black", linewidth=0.5)
    max_mape = float(pooled["mape_pct"].max())
    # Reserve 45% of the x-range on the right for the value labels so
    # "1.59%  (Δ +1.54)" fits inside the axis frame.
    ax_a.set_xlim(0.0, max_mape * 1.45)
    for bar, val, dlt in zip(bars, pooled["mape_pct"], pooled["delta_vs_baseline_pct"]):
        label = f"{val:.2f}%" if abs(dlt) < 0.005 else f"{val:.2f}%  (Δ {dlt:+.2f})"
        ax_a.text(bar.get_width() + 0.02 * max_mape,
                  bar.get_y() + bar.get_height() / 2,
                  label, va="center", fontsize=8)
    ax_a.set_xlabel("Pooled MAPE (%) with this source zeroed")
    ax_a.set_title("(a) Ablation — which noise carries the budget?")
    ax_a.grid(True, axis="x", alpha=0.25)

    # --- (b) Predicted Bland-Altman ---
    ax_b = fig.add_subplot(gs[0, 1])
    rates = sorted(df["flow_rate_target_mlh"].unique())
    colors_b = plt.cm.viridis(np.linspace(0.20, 0.85, len(rates)))
    for rate, color in zip(rates, colors_b):
        sub = df[df["flow_rate_target_mlh"] == rate]
        # subsample for scatter readability without distorting LoA estimates
        sub_plot = sub.sample(min(1500, len(sub)), random_state=0)
        diff = sub_plot["v_est_ul"].to_numpy() - sub_plot["v_true_ul"].to_numpy()
        mean_xy = (sub_plot["v_est_ul"].to_numpy() + sub_plot["v_true_ul"].to_numpy()) / 2
        ax_b.scatter(mean_xy, diff, s=6, alpha=0.12,
                     color=color, label=f"{rate:.0f} mL/hr")
    full_diff = df["v_est_ul"].to_numpy() - df["v_true_ul"].to_numpy()
    bias = float(np.mean(full_diff))
    sd = float(np.std(full_diff, ddof=1))
    ax_b.axhline(bias, color="black", lw=1.4,
                 label=f"Predicted bias = {bias:+.2f} µL")
    ax_b.axhline(bias + 1.96 * sd, color="firebrick", lw=1.0, ls="--",
                 label=f"Predicted 95% LoA = ±{1.96 * sd:.2f} µL")
    ax_b.axhline(bias - 1.96 * sd, color="firebrick", lw=1.0, ls="--")
    ax_b.axhline(0, color="lightgrey", lw=0.7, zorder=0)
    ax_b.set_xlabel("Mean of device estimate and true drop volume (µL)")
    ax_b.set_ylabel("Device estimate − true (µL)")
    ax_b.set_title("(b) Predicted Bland-Altman — overlay bench data here")
    leg = ax_b.legend(loc="upper right", fontsize=8, framealpha=0.92)
    for handle in leg.legend_handles[:len(rates)]:
        handle.set_alpha(1.0)
        handle.set_sizes([36])
    ax_b.grid(True, alpha=0.25)

    # --- (c) Calibration convergence: SD(V_cal) vs N drops used ---
    ax_c = fig.add_subplot(gs[0, 2])
    if convergence_df is None:
        convergence_df = calibration_convergence(params)
    ax_c.plot(convergence_df["n_drops"], convergence_df["sd_pct"],
              "o-", color="#2e7eb8", lw=1.6, markersize=4, zorder=3,
              label="SD of trimmed-mean V_cal")
    # Firmware default CAL_N=10
    cal_n_firmware = 10
    match = convergence_df.loc[convergence_df["n_drops"] == cal_n_firmware]
    if not match.empty:
        cal_sd_pct = float(match["sd_pct"].iloc[0])
        ax_c.axvline(cal_n_firmware, color="firebrick", lw=1.2, ls="--",
                     label=f"Firmware CAL_N=10 → SD={cal_sd_pct:.2f}%")
    # 1% accuracy target line
    ax_c.axhline(1.0, color="gray", lw=0.8, ls=":", label="1% target")
    ax_c.set_xlabel("N drops used (trim 1 lowest + 1 highest)")
    ax_c.set_ylabel("SD of V_cal (% of drop volume)")
    ax_c.set_title("(c) Calibration convergence (per-board, 50 mL/hr)")
    ax_c.set_xlim(1, float(convergence_df["n_drops"].max()))
    ax_c.set_ylim(bottom=0)
    ax_c.legend(fontsize=8, loc="upper right", framealpha=0.92)
    ax_c.grid(True, alpha=0.25)

    suptitle = (f"A priori MC error budget — "
                f"d={params.d_mean_mm:.1f} mm  ·  "
                f"V̄={params.drop_volume_mean_ul:.0f} µL ± {params.drop_volume_cv*100:.0f}%  ·  "
                f"alignment ±{params.alignment_sd_mm*np.sqrt(3):.1f} mm rect.")
    if title_suffix:
        suptitle += f"   {title_suffix}"
    fig.suptitle(suptitle, fontsize=10)
    return fig


def overlay_bench_points(
    ax: plt.Axes,
    bench_df: pd.DataFrame,
    device_col: str = "v_est_ul",
    truth_col: str = "v_true_ul",
) -> None:
    """Overlay real bench drops on the predicted Bland-Altman axis.

    Call after make_figure() once real data exists. Adds points in
    a distinct marker (black-edged red triangles) so the overlay is
    obvious vs the predicted cloud.
    """
    device = bench_df[device_col].to_numpy()
    truth = bench_df[truth_col].to_numpy()
    diff = device - truth
    mean_xy = (device + truth) / 2
    ax.scatter(mean_xy, diff, marker="^", s=46, color="#d62728",
               edgecolor="black", linewidth=0.5, alpha=0.92,
               label=f"Bench (N={len(bench_df)})", zorder=5)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.92)


def write_sample_csv(df: pd.DataFrame, path: str, per_rate: int = 500,
                     seed: int = DEFAULT_SEED) -> None:
    """Write a small sub-sample of the synthetic data for cold-clone reproducibility.

    Stratified by flow rate. Reproducible via fixed seed.
    """
    rng = np.random.default_rng(seed)
    sub = (df.groupby("flow_rate_target_mlh", group_keys=False)
             .apply(lambda g: g.sample(min(per_rate, len(g)),
                                        random_state=rng.integers(0, 2**32 - 1))))
    sub.to_csv(path, index=False)


if __name__ == "__main__":
    import argparse
    import os
    from pathlib import Path

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--figures-dir", default="../figures",
                    help="Where to write fig_error_budget.png")
    ap.add_argument("--sample-dir", default="../../data/sample",
                    help="Where to write error_budget_synthetic.csv")
    ap.add_argument("--n-campaigns", type=int, default=DEFAULT_MC_CAMPAIGNS)
    ap.add_argument("--ablation-campaigns", type=int, default=DEFAULT_ABLATION_CAMPAIGNS)
    args = ap.parse_args()

    figures_dir = Path(args.figures_dir).resolve()
    sample_dir = Path(args.sample_dir).resolve()
    figures_dir.mkdir(parents=True, exist_ok=True)
    sample_dir.mkdir(parents=True, exist_ok=True)

    params = default_params()
    print("Parameters:")
    for k, v in params.__dict__.items():
        print(f"  {k} = {v}")

    print(f"\nSimulating {args.n_campaigns} campaigns...")
    df = simulate(params, n_campaigns=args.n_campaigns)
    print(f"  {len(df):,} synthetic drops across {df['run_id'].nunique():,} runs")

    print("\nPer-rate predicted error:")
    print(summarise(df).to_string(index=False))

    print(f"\nAblation ({args.ablation_campaigns} campaigns per source)...")
    abl = ablation(params, n_campaigns=args.ablation_campaigns)
    pooled = abl[abl["rate_mlh"] == "all"].sort_values("mape_pct")
    print(pooled[["source", "mape_pct", "delta_vs_baseline_pct"]].to_string(index=False))

    print("\nCalibration convergence (per-board, 50 mL/hr)...")
    conv = calibration_convergence(params, n_drops_max=30, n_bootstrap=2000)
    cal10 = conv.loc[conv["n_drops"] == 10]
    if not cal10.empty:
        print(f"  CAL_N=10 (firmware default): SD(V_cal) = "
              f"{float(cal10['sd_v_cal_ul'].iloc[0]):.3f} µL "
              f"= {float(cal10['sd_pct'].iloc[0]):.2f}% of {params.drop_volume_mean_ul:.0f} µL")

    fig = make_figure(df, abl, params, convergence_df=conv)
    fig_path = figures_dir / "fig_error_budget.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nFigure: {fig_path}")

    sample_path = sample_dir / "error_budget_synthetic.csv"
    write_sample_csv(df, str(sample_path))
    print(f"Sample CSV: {sample_path}")
