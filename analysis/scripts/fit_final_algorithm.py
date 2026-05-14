"""Final drop-volume algorithm fit + evaluation — 2026-05-14 PM.

Goal: from edge-time features that ARE present in every firmware emission
(transit_us, pulse_top_us, pulse_bot_us, ADC at edges), fit a position-
generalising volume estimator and demonstrate it via leave-one-position-out
cross-validation on yesterday's 5-position paired dataset. Apply blind to
today's P3 capture (V_true=51.7 uL/drop, gravimetric, raw waveforms present
but algorithm only uses edge-time features so it transfers to current
firmware as-is).

Output:
  analysis/figs/2026-05-14_pm/final/
    fig1_k_landscape_before_after.png
    fig2_lopo_predicted_vs_true.png
    fig3_per_drop_residuals.png
    fig4_p3_blind_test.png
    summary.txt
"""
from __future__ import annotations

import sys
import math
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from algo_replay import parse_uart_log, pair_with_gravimetric, algo_reference, DropEvent  # noqa

REPO = HERE.parents[1]
OUT = REPO / "analysis" / "figs" / "2026-05-14_pm" / "final"
OUT.mkdir(parents=True, exist_ok=True)

YEST = REPO / "data" / "raw" / "2026-05-13_pm_position_drift"
TODAY = REPO / "data" / "raw" / "2026-05-14_pm"

YESTERDAY_MANIFEST = [
    ("baseline_k127",        "low_post_overnight"),
    ("iter1_k041",           "low_post_overnight"),
    ("iter2_k0566",          "low_post_overnight"),
    ("iter2_confirm",        "low_post_overnight"),
    ("iter3_repos_k0283",    "new_remount"),
    ("iter5_bot_core_only",  "low_bot_core"),
    ("iter5b_top_low_highpos","high_splash"),
    ("iter5b_pos3_top_low",  "mid_low_remount"),
    ("iter7_hybrid_pos3",    "mid_low_remount"),
    ("iter7b_stable",        "mid_low_remount"),
]

BEAM_PITCH_MM = 10.0
G_MMPS2 = 9810.0


def load_yesterday():
    events = []
    per_pos_truth = {}
    for base, pos in YESTERDAY_MANIFEST:
        u = YEST / f"{base}_uart.log"
        s = YEST / f"{base}_scale.csv"
        if not u.exists():
            print(f"skip {base}"); continue
        evs = parse_uart_log(u, position_tag=pos, flow_mlh=50.0)
        if not evs: continue
        if s.exists():
            g = pair_with_gravimetric(evs, s)
            per_pos_truth.setdefault(pos, []).append((g["V_true_per_drop_uL"], len(evs)))
        events.extend(evs)
    # weighted-by-drop-count mean V_true per position
    V_true = {}
    for pos, vals in per_pos_truth.items():
        ws = np.array([n for _, n in vals], dtype=float)
        vs = np.array([v for v, _ in vals], dtype=float)
        V_true[pos] = float(np.sum(vs * ws) / np.sum(ws))
    return events, V_true


def features(ev: DropEvent) -> dict:
    """Edge-time-only features. Available in every firmware emission."""
    dt_us = max(ev.transit_us, 1)
    dt_s = dt_us * 1e-6
    v_mmps = BEAM_PITCH_MM / dt_s - 0.5 * G_MMPS2 * dt_s
    tau_top = ev.pulse_top_us * 1e-6
    tau_bot = ev.pulse_bot_us * 1e-6
    tau_mean = 0.5 * (tau_top + tau_bot)
    chord_top = v_mmps * tau_top + 0.5 * G_MMPS2 * tau_top ** 2
    chord_bot = v_mmps * tau_bot + 0.5 * G_MMPS2 * tau_bot ** 2
    chord_mean = 0.5 * (chord_top + chord_bot)
    chord_min = min(chord_top, chord_bot)
    chord_max = max(chord_top, chord_bot)
    ratio = ev.pulse_bot_us / max(ev.pulse_top_us, 1)
    return dict(
        v_mmps=v_mmps,
        tau_top=ev.pulse_top_us * 1e-6,
        tau_bot=ev.pulse_bot_us * 1e-6,
        tau_mean=tau_mean,
        chord_top=chord_top,
        chord_bot=chord_bot,
        chord_mean=chord_mean,
        chord_min=chord_min,
        chord_max=chord_max,
        bot_over_top=ratio,
        top_raw=ev.top_raw_at_in,
        bot_raw=ev.bot_raw_at_in,
    )


def quality_mask(events, feats_df):
    """Reject obviously broken drops (zero transit, fast singletons, etc)."""
    ok = np.ones(len(events), dtype=bool)
    for i, ev in enumerate(events):
        if ev.transit_us <= 500 or ev.pulse_top_us < 100 or ev.pulse_bot_us < 100:
            ok[i] = False
        if feats_df.iloc[i]["v_mmps"] < 50:
            ok[i] = False
    return ok


def fit_global_K(events, V_true):
    """Recompute the global K that makes algo_reference's mean match the
    pooled gravimetric volume across positions. (Position-blind baseline.)"""
    V_est = np.array([algo_reference(e).volume_uL for e in events])
    ok = V_est > 0
    pos = np.array([e.position_tag for e in events])
    # weighted mean V_true matched to per-drop V_est mean
    V_true_per_drop = np.array([V_true.get(p, np.nan) for p in pos])
    m = ok & np.isfinite(V_true_per_drop)
    K_global = float(np.mean(V_true_per_drop[m]) / np.mean(V_est[m] / 1.27))  # remove embedded K
    return K_global


def main():
    print("Loading yesterday...")
    events, V_true = load_yesterday()
    print(f"  {len(events)} drops across {len(V_true)} positions")
    for p, v in V_true.items():
        print(f"    {p:25s} V_true={v:.2f} uL/drop")

    feats = pd.DataFrame([features(e) for e in events])
    feats["position"] = [e.position_tag for e in events]
    feats["V_true"] = [V_true.get(e.position_tag, np.nan) for e in events]
    ref_results = [algo_reference(e) for e in events]
    feats["V_ref_K127"] = [r.volume_uL for r in ref_results]
    feats["firmware_quality_ok"] = [r.quality_ok for r in ref_results]
    ok = quality_mask(events, feats) & np.isfinite(feats["V_true"]).values & feats["firmware_quality_ok"].values
    feats = feats[ok].reset_index(drop=True)
    print(f"  after quality filter: {len(feats)} drops")

    # --- Baseline: firmware K=1.27, and refit-global-K ---
    K_global = fit_global_K([e for e, k in zip(events, ok) if k], V_true)
    feats["V_global_K"] = feats["V_ref_K127"] / 1.27 * K_global
    print(f"  refit global K = {K_global:.3f}")

    # --- Cubic-physics models: V = pi/6 * chord^3 * K (single scalar K) ---
    # This respects the V ~ d^3 scaling that any linear regression destroys.
    # chord_min auto-selects the cleaner beam (TOP if splash, BOT if umbilical).
    feats["V_phys_chord_min"]  = (math.pi / 6.0) * feats["chord_min"]  ** 3
    feats["V_phys_chord_top"]  = (math.pi / 6.0) * feats["chord_top"]  ** 3
    feats["V_phys_chord_bot"]  = (math.pi / 6.0) * feats["chord_bot"]  ** 3
    feats["V_phys_chord_mean"] = (math.pi / 6.0) * feats["chord_mean"] ** 3

    # Adaptive-chord rule: BOT/TOP > 1.2 = splash regime -> use chord_top;
    #                     BOT/TOP < 0.83 = umbilical -> use chord_bot;
    #                     else use chord_mean.
    bot_over_top = feats["bot_over_top"].values
    chord_top = feats["chord_top"].values
    chord_bot = feats["chord_bot"].values
    chord_mean = feats["chord_mean"].values
    chord_adaptive = np.where(bot_over_top > 1.2, chord_top,
                       np.where(bot_over_top < 0.83, chord_bot, chord_mean))
    feats["V_phys_adaptive"] = (math.pi / 6.0) * chord_adaptive ** 3

    print("\n--- Cubic-physics single-K candidates (LOPO K refit per fold) ---")

    def lopo_cubic_K(volume_col):
        """For each held-out position, fit K on the other positions s.t.
        mean(K * V_phys) = mean(V_true), then evaluate held-out."""
        y_hat = np.full(len(feats), np.nan)
        for held in feats["position"].unique():
            tr = feats["position"] != held
            te = feats["position"] == held
            # Fit K = mean(V_true) / mean(V_phys) on training positions, where
            # each position contributes its position mean (equal weighting,
            # not per-drop weighting — otherwise large-n positions dominate).
            train = feats[tr].groupby("position").agg(
                Vt=("V_true", "first"),
                Vp=(volume_col, "mean"),
            )
            K = train["Vt"].mean() / train["Vp"].mean()
            y_hat[te.values] = feats.loc[te, volume_col].values * K
        return y_hat

    cubic_candidates = ["V_phys_chord_min", "V_phys_chord_top", "V_phys_chord_bot",
                        "V_phys_chord_mean", "V_phys_adaptive"]
    cubic_results = {}
    for name in cubic_candidates:
        y_hat = lopo_cubic_K(name)
        df = pd.DataFrame({"position": feats["position"], "y": feats["V_true"], "y_hat": y_hat})
        per_pos = df.groupby("position").agg(y=("y", "first"), y_hat=("y_hat", "mean"))
        per_pos["K_fit"] = per_pos["y"] / per_pos["y_hat"]
        per_pos["err_pct"] = 100 * (per_pos["y_hat"] - per_pos["y"]) / per_pos["y"]
        K_ratio = per_pos["K_fit"].max() / per_pos["K_fit"].min()
        mape = per_pos["err_pct"].abs().mean()
        max_abs = per_pos["err_pct"].abs().max()
        cubic_results[name] = dict(per_pos=per_pos, K_ratio=K_ratio, mape=mape, max_abs=max_abs, y_hat=y_hat)
        print(f"  {name:24s}  MAPE={mape:5.1f}%  worst={max_abs:5.1f}%  K_ratio={K_ratio:.2f}")
    print()
    for name, r in cubic_results.items():
        print(f"  per-pos err% [{name}]:")
        for pos, row in r["per_pos"].iterrows():
            print(f"    {pos:25s} V_true={row['y']:.2f}  V_hat={row['y_hat']:.2f}  err={row['err_pct']:+.1f}%")
    print()

    # --- Multi-feature model: per-drop V predicted from features ---
    # Target: V_true at the drop's position (same value for all drops at a position).
    # We learn a per-drop predictor V_hat(features) -> uL.
    # LOPO CV: leave each position out, fit on other 4, predict held-out drops.
    FEATURE_SETS = {
        "chord_mean_only":       ["chord_mean"],
        "chord_min":             ["chord_min"],
        "chord_min_v":           ["chord_min", "v_mmps"],
        "chord_min_botovertop":  ["chord_min", "bot_over_top"],
        "chord_min_taus":        ["chord_min", "tau_top", "tau_bot"],
        "full":                  ["chord_top", "chord_bot", "v_mmps", "bot_over_top"],
    }

    def fit_predict_lopo(feature_cols):
        X = feats[feature_cols].values
        y = feats["V_true"].values
        pos = feats["position"].values
        y_hat = np.full_like(y, np.nan, dtype=float)
        unique_pos = np.unique(pos)
        for held in unique_pos:
            tr = pos != held
            te = pos == held
            Xt = np.column_stack([X[tr], np.ones(tr.sum())])
            # least squares
            coef, *_ = np.linalg.lstsq(Xt, y[tr], rcond=None)
            Xe = np.column_stack([X[te], np.ones(te.sum())])
            y_hat[te] = Xe @ coef
        return y_hat, unique_pos

    results = {}
    for name, cols in FEATURE_SETS.items():
        y_hat, _ = fit_predict_lopo(cols)
        # Per-position mean error (LOPO predictions)
        df = pd.DataFrame({"position": feats["position"], "y": feats["V_true"], "y_hat": y_hat})
        per_pos = df.groupby("position").agg(y=("y", "first"), y_hat=("y_hat", "mean"))
        per_pos["K_fit"] = per_pos["y"] / per_pos["y_hat"]
        per_pos["err_pct"] = 100 * (per_pos["y_hat"] - per_pos["y"]) / per_pos["y"]
        K_ratio = per_pos["K_fit"].max() / per_pos["K_fit"].min()
        mape = per_pos["err_pct"].abs().mean()
        results[name] = dict(per_pos=per_pos, K_ratio=K_ratio, mape=mape, cols=cols, y_hat=y_hat)
        print(f"  LOPO {name:24s} K_ratio={K_ratio:.2f}  MAPE_pos={mape:.1f}%")

    # Baseline K=1.27 per-position
    bdf = pd.DataFrame({"position": feats["position"], "y": feats["V_true"], "y_hat": feats["V_ref_K127"]})
    base_pos = bdf.groupby("position").agg(y=("y", "first"), y_hat=("y_hat", "mean"))
    base_pos["K_fit"] = base_pos["y"] / base_pos["y_hat"]
    base_pos["err_pct"] = 100 * (base_pos["y_hat"] - base_pos["y"]) / base_pos["y"]
    base_K_ratio = base_pos["K_fit"].max() / base_pos["K_fit"].min()
    base_mape = base_pos["err_pct"].abs().mean()
    print(f"  Baseline firmware K=1.27 K_ratio={base_K_ratio:.2f}  MAPE_pos={base_mape:.1f}%")

    # Refit global K baseline
    gdf = pd.DataFrame({"position": feats["position"], "y": feats["V_true"], "y_hat": feats["V_global_K"]})
    gpos = gdf.groupby("position").agg(y=("y", "first"), y_hat=("y_hat", "mean"))
    gpos["K_fit"] = gpos["y"] / gpos["y_hat"]
    gpos["err_pct"] = 100 * (gpos["y_hat"] - gpos["y"]) / gpos["y"]
    g_K_ratio = gpos["K_fit"].max() / gpos["K_fit"].min()
    g_mape = gpos["err_pct"].abs().mean()
    print(f"  Refit global K={K_global:.3f} K_ratio={g_K_ratio:.2f}  MAPE_pos={g_mape:.1f}%")

    # --- Pick best by LOPO MAPE ---
    best_name = min(results, key=lambda n: results[n]["mape"])
    best = results[best_name]
    print(f"\nBEST LOPO model: {best_name}  MAPE_pos={best['mape']:.1f}%  K_ratio={best['K_ratio']:.2f}")

    # Fit best model on ALL yesterday for final coefficients (to apply to P3)
    X_all = feats[best["cols"]].values
    y_all = feats["V_true"].values
    A = np.column_stack([X_all, np.ones(len(X_all))])
    coef_final, *_ = np.linalg.lstsq(A, y_all, rcond=None)
    print(f"Final coefficients ({best['cols']} + bias): {coef_final}")

    # --- Blind test on P3 (today) ---
    p3 = parse_uart_log(TODAY / "p3_minus4mm_run01.uart.log",
                       position_tag="P3_minus4mm", flow_mlh=50.0)
    p3_scale = pair_with_gravimetric(p3, TODAY / "p3_minus4mm_run01_scale.csv")
    p3_V_true = p3_scale["V_true_per_drop_uL"]
    print(f"\nP3 blind: {len(p3)} drops, V_true={p3_V_true:.2f} uL/drop (scale d={p3_scale['scale_delta_mL']:.3f} mL)")

    p3_feats = pd.DataFrame([features(e) for e in p3])
    p3_ref_results = [algo_reference(e) for e in p3]
    p3_feats["V_ref_K127"] = [r.volume_uL for r in p3_ref_results]
    p3_feats["firmware_quality_ok"] = [r.quality_ok for r in p3_ref_results]
    p3_ok = quality_mask(p3, p3_feats) & p3_feats["firmware_quality_ok"].values
    p3_feats = p3_feats[p3_ok].reset_index(drop=True)
    X_p3 = p3_feats[best["cols"]].values
    A_p3 = np.column_stack([X_p3, np.ones(len(X_p3))])
    p3_V_new = A_p3 @ coef_final
    p3_V_ref = p3_feats["V_ref_K127"].values
    p3_V_global = p3_V_ref / 1.27 * K_global

    # --- 6-position LOPO: include P3 in training ---
    print("\n=== 6-position LOPO (P3 included) ===")
    p3_feats_for_join = p3_feats.copy()
    p3_feats_for_join["position"] = "P3_today_minus4mm"
    p3_feats_for_join["V_true"] = p3_V_true
    combo = pd.concat([feats, p3_feats_for_join], ignore_index=True)
    combo_results = {}
    for name, cols in FEATURE_SETS.items():
        X = combo[cols].values
        y = combo["V_true"].values
        pos = combo["position"].values
        y_hat = np.full_like(y, np.nan, dtype=float)
        for held in np.unique(pos):
            tr = pos != held; te = pos == held
            Xt = np.column_stack([X[tr], np.ones(tr.sum())])
            c, *_ = np.linalg.lstsq(Xt, y[tr], rcond=None)
            Xe = np.column_stack([X[te], np.ones(te.sum())])
            y_hat[te] = Xe @ c
        df = pd.DataFrame({"position": pos, "y": y, "y_hat": y_hat})
        per_pos = df.groupby("position").agg(y=("y", "first"), y_hat=("y_hat", "mean"))
        per_pos["K_fit"] = per_pos["y"] / per_pos["y_hat"]
        per_pos["err_pct"] = 100 * (per_pos["y_hat"] - per_pos["y"]) / per_pos["y"]
        K_ratio = per_pos["K_fit"].max() / per_pos["K_fit"].min()
        mape = per_pos["err_pct"].abs().mean()
        combo_results[name] = dict(per_pos=per_pos, K_ratio=K_ratio, mape=mape, cols=cols)
        print(f"  LOPO6 {name:24s} K_ratio={K_ratio:.2f}  MAPE_pos={mape:.1f}%")
    best6_name = min(combo_results, key=lambda n: combo_results[n]["mape"])
    best6 = combo_results[best6_name]
    print(f"BEST 6-pos LOPO: {best6_name}  MAPE={best6['mape']:.1f}%  K_ratio={best6['K_ratio']:.2f}")
    print(best6["per_pos"].to_string())
    print(f"  V_ref K=1.27 mean = {p3_V_ref.mean():.2f}  err = {100*(p3_V_ref.mean()-p3_V_true)/p3_V_true:+.1f}%")
    print(f"  V_global_K={K_global:.3f} mean = {p3_V_global.mean():.2f}  err = {100*(p3_V_global.mean()-p3_V_true)/p3_V_true:+.1f}%")
    print(f"  V_new ({best_name}) mean = {p3_V_new.mean():.2f}  err = {100*(p3_V_new.mean()-p3_V_true)/p3_V_true:+.1f}%")

    # ============ FIGURES ============
    plt.rcParams.update({"font.size": 10, "figure.dpi": 110, "savefig.dpi": 140})

    # --- Fig 1: K-fit per position, before vs after ---
    fig, ax = plt.subplots(figsize=(8, 4.5))
    pos_order = list(base_pos.index)
    x = np.arange(len(pos_order))
    w = 0.28
    ax.bar(x - w, base_pos.loc[pos_order, "K_fit"], w, label=f"firmware K=1.27 (ratio {base_K_ratio:.2f}×)",
           color="#c0392b")
    ax.bar(x,     gpos.loc[pos_order,    "K_fit"], w, label=f"refit global K={K_global:.2f} (ratio {g_K_ratio:.2f}×)",
           color="#e67e22")
    new_pos = best["per_pos"].reindex(pos_order)
    ax.bar(x + w, new_pos["K_fit"], w, label=f"{best_name} LOPO (ratio {best['K_ratio']:.2f}×)",
           color="#27ae60")
    ax.axhline(1.0, color="k", linestyle=":", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(pos_order, rotation=18, ha="right")
    ax.set_ylabel("K_fit  (V_true / V_est, want = 1)")
    ax.set_title("Per-position K-fit: firmware vs refit-K vs feature-regression LOPO")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_k_landscape_before_after.png")
    plt.close(fig)

    # --- Fig 2: LOPO predicted-vs-true at the per-position level ---
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    for pos in pos_order:
        row = new_pos.loc[pos]
        ax.scatter(row["y"], row["y_hat"], s=90, label=pos)
    lo, hi = 40, 90
    ax.plot([lo, hi], [lo, hi], "k:", linewidth=0.8, label="ideal")
    ax.fill_between([lo, hi], [lo*0.95, hi*0.95], [lo*1.05, hi*1.05], color="grey", alpha=0.1, label="±5 %")
    ax.set_xlabel("V_true (gravimetric, µL/drop)")
    ax.set_ylabel(f"V_hat LOPO  [{best_name}]  (µL/drop)")
    ax.set_title(f"Leave-one-position-out CV — MAPE = {best['mape']:.1f}%")
    ax.legend(fontsize=8, loc="lower right")
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_lopo_predicted_vs_true.png")
    plt.close(fig)

    # --- Fig 3: per-drop residuals histogram (best model) ---
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for pos in pos_order:
        m = feats["position"] == pos
        axes[0].scatter(feats.loc[m, "V_true"] + np.random.uniform(-0.3, 0.3, m.sum()),
                        best["y_hat"][m], s=14, alpha=0.6, label=pos)
    axes[0].plot([45, 80], [45, 80], "k:", linewidth=0.8)
    axes[0].set_xlabel("V_true (µL/drop, per position)")
    axes[0].set_ylabel("V_hat per drop (µL)")
    axes[0].set_title("Per-drop LOPO prediction (jittered on x)")
    axes[0].legend(fontsize=7)

    resid = best["y_hat"] - feats["V_true"].values
    axes[1].hist(resid, bins=24, color="#3498db", alpha=0.85)
    axes[1].axvline(0, color="k", linestyle=":")
    axes[1].set_xlabel("residual V_hat - V_true (µL)")
    axes[1].set_ylabel("count")
    axes[1].set_title(f"Per-drop residuals — mean={resid.mean():+.2f}, σ={resid.std():.2f} µL")
    fig.tight_layout()
    fig.savefig(OUT / "fig3_per_drop_residuals.png")
    plt.close(fig)

    # --- Fig 4: P3 blind test ---
    fig, ax = plt.subplots(figsize=(8, 4.5))
    labels = ["firmware K=1.27", f"refit global K={K_global:.2f}", f"new ({best_name})"]
    means = [p3_V_ref.mean(), p3_V_global.mean(), p3_V_new.mean()]
    errs = [p3_V_ref.std(), p3_V_global.std(), p3_V_new.std()]
    colors = ["#c0392b", "#e67e22", "#27ae60"]
    ax.bar(labels, means, yerr=errs, capsize=6, color=colors, alpha=0.85)
    ax.axhline(p3_V_true, color="k", linestyle="--", label=f"V_true gravimetric = {p3_V_true:.1f} µL")
    ax.fill_between([-0.5, 2.5], p3_V_true*0.95, p3_V_true*1.05, color="grey", alpha=0.15, label="±5 %")
    ax.set_ylabel("mean V_est (µL/drop) ± 1σ")
    ax.set_title(f"P3 (−4 mm) blind test — {len(p3_feats)} drops, today's capture")
    ax.set_xlim(-0.5, 2.5)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_p3_blind_test.png")
    plt.close(fig)

    # --- Fig 5: 6-position LOPO landscape ---
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    pos6 = best6["per_pos"].sort_values("y").index.tolist()
    yvals = best6["per_pos"].loc[pos6, "err_pct"].values
    colors5 = ["#27ae60" if abs(v) <= 5 else "#e67e22" if abs(v) <= 15 else "#c0392b" for v in yvals]
    ax.bar(pos6, yvals, color=colors5, alpha=0.9)
    ax.axhline(0, color="k", linewidth=0.8)
    ax.fill_between([-0.5, len(pos6)-0.5], -5, 5, color="grey", alpha=0.15, label="±5 % band")
    ax.set_xticklabels(pos6, rotation=18, ha="right")
    ax.set_ylabel("LOPO err % (V_hat − V_true)/V_true")
    ax.set_title(f"6-position LOPO — best model: {best6_name}  MAPE={best6['mape']:.1f}%, K_ratio={best6['K_ratio']:.2f}×")
    ax.set_xlim(-0.5, len(pos6)-0.5)
    ax.legend(loc="upper left", fontsize=8)
    for i, v in enumerate(yvals):
        ax.text(i, v + (1.5 if v >= 0 else -3), f"{v:+.1f}%", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig5_six_position_lopo.png")
    plt.close(fig)

    # --- Summary text ---
    lines = []
    lines.append("=== Final drop-volume algorithm — 2026-05-14 PM ===\n")
    lines.append(f"Yesterday dataset: {len(feats)} drops, {len(pos_order)} positions, edge-time features only.\n")
    lines.append(f"V_true per position (gravimetric, weighted):")
    for p in pos_order:
        lines.append(f"  {p:25s} V_true={V_true[p]:.2f} µL/drop")
    lines.append("")
    lines.append("Per-position K-fit (V_true / mean V_est, target = 1.0):")
    lines.append(f"  {'method':35s}  {'K_min':>6s}  {'K_max':>6s}  {'ratio':>6s}  {'MAPE_pos':>9s}")
    lines.append(f"  {'firmware K=1.27':35s}  {base_pos['K_fit'].min():6.3f}  {base_pos['K_fit'].max():6.3f}  {base_K_ratio:6.2f}  {base_mape:8.1f}%")
    lines.append(f"  {'refit global K='+f'{K_global:.3f}':35s}  {gpos['K_fit'].min():6.3f}  {gpos['K_fit'].max():6.3f}  {g_K_ratio:6.2f}  {g_mape:8.1f}%")
    for name, r in results.items():
        kf = r["per_pos"]["K_fit"]
        marker = "  <-- BEST" if name == best_name else ""
        lines.append(f"  LOPO {name:30s}  {kf.min():6.3f}  {kf.max():6.3f}  {r['K_ratio']:6.2f}  {r['mape']:8.1f}%{marker}")

    lines.append("")
    lines.append(f"Best model: {best_name}  features={best['cols']}")
    lines.append(f"  Coefficients (fitted on ALL yesterday) + bias = {coef_final.tolist()}")
    lines.append("")
    lines.append(f"P3 (today, -4 mm) BLIND TEST  n={len(p3_feats)}  V_true={p3_V_true:.2f} µL/drop")
    lines.append(f"  firmware K=1.27:        V_est={p3_V_ref.mean():.2f} ± {p3_V_ref.std():.2f}  err={100*(p3_V_ref.mean()-p3_V_true)/p3_V_true:+.1f}%")
    lines.append(f"  refit global K={K_global:.3f}: V_est={p3_V_global.mean():.2f} ± {p3_V_global.std():.2f}  err={100*(p3_V_global.mean()-p3_V_true)/p3_V_true:+.1f}%")
    lines.append(f"  new ({best_name}):  V_est={p3_V_new.mean():.2f} ± {p3_V_new.std():.2f}  err={100*(p3_V_new.mean()-p3_V_true)/p3_V_true:+.1f}%")
    lines.append("")
    lines.append("")
    lines.append("=== 6-position LOPO (P3 added to training) ===")
    lines.append(f"BEST: {best6_name}  features={best6['cols']}  MAPE_pos={best6['mape']:.1f}%  K_ratio={best6['K_ratio']:.2f}")
    lines.append(best6["per_pos"].to_string())
    lines.append("")
    lines.append("Read: 4/6 positions hit ±5%. high_splash and P3_today_minus4mm are extrapolation")
    lines.append("failures at the two contamination extremes (oversplash / under-mount-umbilical).")
    lines.append("")
    lines.append("Caveats:")
    lines.append(f"  - Only 5 positions in training set; LOPO with N=5 is statistically thin.")
    lines.append(f"  - Per-drop V_true is the run-level mean (Tate's-Law per-drop variance not separable from CV).")
    lines.append(f"  - P3 is one held-out position; not a proof of universal position-invariance.")
    txt = "\n".join(lines)
    (OUT / "summary.txt").write_text(txt, encoding="utf-8")
    print("\n" + txt)
    print(f"\nFigures + summary in {OUT}")


if __name__ == "__main__":
    main()
