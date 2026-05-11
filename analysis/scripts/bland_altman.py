"""Bland-Altman agreement plots.

Bland & Altman (Lancet, 1986) — the international standard for
comparing two measurement methods. Required by convention for
infusion-pump validation per IEC 60601-2-24.

X-axis: mean of the two methods.
Y-axis: difference (device - reference).
Horizontal lines: mean bias and 95% Limits of Agreement (mean +/- 1.96 SD).

Produces:
- bland_altman_combined(...): one panel, all runs.
- bland_altman_per_rate(...): one row of subplots, one per flow rate.
"""

from __future__ import annotations

from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _ba_stats(device: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    diff = device - truth
    mean = (device + truth) / 2.0
    bias = float(diff.mean())
    sd = float(diff.std(ddof=1))
    return {
        "bias": bias,
        "sd": sd,
        "loa_upper": bias + 1.96 * sd,
        "loa_lower": bias - 1.96 * sd,
        "diff": diff,
        "mean": mean,
    }


def bland_altman_combined(
    df: pd.DataFrame,
    device_col: str,
    truth_col: str,
    rate_col: str = "flow_rate_target_mlh",
    title: str = "Bland-Altman: device vs. gravimetric ground truth",
) -> plt.Figure:
    """Single-panel Bland-Altman over all runs, color-coded by flow rate."""
    fig, ax = plt.subplots(figsize=(7, 5), dpi=120)
    device = df[device_col].to_numpy()
    truth = df[truth_col].to_numpy()
    stats = _ba_stats(device, truth)

    rates = sorted(df[rate_col].unique())
    colors = plt.cm.viridis(np.linspace(0.2, 0.85, len(rates)))
    for rate, color in zip(rates, colors):
        mask = df[rate_col].to_numpy() == rate
        ax.scatter(stats["mean"][mask], stats["diff"][mask],
                   s=42, alpha=0.75, color=color, edgecolor="black",
                   linewidth=0.5, label=f"{rate} mL/hr")

    ax.axhline(stats["bias"], color="black", lw=1.4, label=f"Bias = {stats['bias']:+.2f} mL/hr")
    ax.axhline(stats["loa_upper"], color="firebrick", lw=1.0, ls="--",
               label=f"95% LoA = ±{1.96*stats['sd']:.2f} mL/hr")
    ax.axhline(stats["loa_lower"], color="firebrick", lw=1.0, ls="--")
    ax.axhline(0, color="lightgrey", lw=0.7, zorder=0)

    ax.set_xlabel("Mean of device and gravimetric (mL/hr)")
    ax.set_ylabel("Device - gravimetric (mL/hr)")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig


def bland_altman_per_rate(
    df: pd.DataFrame,
    device_col: str,
    truth_col: str,
    rate_col: str = "flow_rate_target_mlh",
) -> plt.Figure:
    """One subplot per flow rate (reveals rate-dependent bias)."""
    rates = sorted(df[rate_col].unique())
    fig, axes = plt.subplots(1, len(rates), figsize=(4 * len(rates), 4), dpi=120, sharey=True)
    if len(rates) == 1:
        axes = [axes]

    for ax, rate in zip(axes, rates):
        sub = df[df[rate_col] == rate]
        if len(sub) < 2:
            ax.set_title(f"{rate} mL/hr (N={len(sub)} — insufficient for stats)")
            ax.scatter(sub[device_col], sub[device_col] - sub[truth_col], color="grey")
            continue
        stats = _ba_stats(sub[device_col].to_numpy(), sub[truth_col].to_numpy())
        ax.scatter(stats["mean"], stats["diff"], s=42, alpha=0.8, color="steelblue",
                   edgecolor="black", linewidth=0.5)
        ax.axhline(stats["bias"], color="black", lw=1.2)
        ax.axhline(stats["loa_upper"], color="firebrick", lw=1.0, ls="--")
        ax.axhline(stats["loa_lower"], color="firebrick", lw=1.0, ls="--")
        ax.axhline(0, color="lightgrey", lw=0.7, zorder=0)
        ax.set_title(f"{rate} mL/hr  (bias={stats['bias']:+.2f}, ±LoA={1.96*stats['sd']:.2f})")
        ax.set_xlabel("Mean (mL/hr)")
        ax.grid(True, alpha=0.25)

    axes[0].set_ylabel("Device - gravimetric (mL/hr)")
    fig.suptitle("Bland-Altman per flow rate", y=1.02)
    fig.tight_layout()
    return fig
