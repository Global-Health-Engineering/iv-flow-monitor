"""Raw beam waveform overlay per position — the §17-grounding figure.

Mandatory figure per the 2026-05-14 PM session plan, regardless of
whether an algorithm wins or not. Overlays the TOP and BOT beam
attenuation traces for ~10 drops at each mount position, time-aligned
on the trigger anchor. The shape differences between positions ARE the
empirical evidence behind §17's umbilical/splash contamination claims.

Generates one figure per position + an all-positions composite. Saves
to analysis/figs/2026-05-14_pm/raw_overlays_*.png.

Run after the 2026-05-14 PM bench captures land:
    python plot_raw_overlays.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from algo_replay import parse_uart_log

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data" / "raw" / "2026-05-14_pm"
OUT_DIR = REPO_ROOT / "analysis" / "figs" / "2026-05-14_pm"

# Map filename stem (without ".uart.log") -> position tag.
# Position tags are used both as the legend label AND as the figure
# filename suffix, so keep them filename-safe (no spaces, no parens).
# Multiple stems can map to the same tag — multi-run captures at one
# mount group into one legend entry on the composite.
TODAY_POSITION_MAP = {
    "p1_high_run01":      "P1_high",
    "p1_high_run02":      "P1_high",
    "p2_minus1mm_run01":  "P2_minus1mm",
    "p2_minus1mm_run02":  "P2_minus1mm",
    "p3_minus4mm_run01":  "P3_minus4mm",
    # p1_high_first_capture intentionally excluded — format-validation
    # probe with 0 drops captured.
}


def _drop_overlay(events, channel: str, ax, n_drops: int = 10,
                  baseline_window: int = 100, alpha: float = 0.5):
    """Overlay up to n_drops of one channel's attenuation traces."""
    drawn = 0
    peaks = []
    for ev in events:
        if not ev.has_raw or drawn >= n_drops:
            continue
        sig = (ev.raw_top if channel == "top" else ev.raw_bot).astype(np.float64)
        t = ev.raw_t_us.astype(np.float64)
        bw = min(baseline_window, sig.size)
        baseline = float(np.mean(sig[:bw]))
        atten = np.maximum(sig - baseline, 0.0)
        # Align on trigger anchor.
        t_rel_ms = (t - ev.t_trigger_us) / 1000.0
        ax.plot(t_rel_ms, atten, alpha=alpha, linewidth=0.8)
        peaks.append(float(np.max(atten)))
        drawn += 1
    ax.set_xlabel("t − t_trigger (ms)")
    ax.set_ylabel(f"{channel.upper()} beam occlusion (ADC counts above baseline)")
    ax.set_title(f"{channel.upper()} beam, n={drawn} drops, peak range {min(peaks):.0f}–{max(peaks):.0f}" if peaks else f"{channel.upper()} beam (no raw data)")
    ax.grid(alpha=0.3)
    ax.axvline(0.0, color="green", linestyle="--", alpha=0.4, linewidth=1)
    return drawn


def plot_one_position(position_tag: str, events, out_dir: Path):
    fig, (ax_top, ax_bot) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f"Raw beam overlay — {position_tag}", fontsize=12)
    n_top = _drop_overlay(events, "top", ax_top)
    n_bot = _drop_overlay(events, "bot", ax_bot)
    fig.tight_layout()
    out_path = out_dir / f"raw_overlays_{position_tag}.png"
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"  {position_tag}: TOP={n_top} BOT={n_bot} -> {out_path}")


def plot_composite(per_position_events: dict, out_dir: Path):
    """One big figure: TOP and BOT, each with all positions overlaid."""
    positions = list(per_position_events.keys())
    colors = plt.cm.tab10(np.linspace(0, 1, max(len(positions), 1)))

    fig, (ax_top, ax_bot) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Raw beam overlays — all positions composite (2026-05-14 PM)", fontsize=13)

    for ax, channel in [(ax_top, "top"), (ax_bot, "bot")]:
        for col, pos in zip(colors, positions):
            evs = per_position_events[pos][:5]   # 5 drops per position
            for j, ev in enumerate(evs):
                if not ev.has_raw:
                    continue
                sig = (ev.raw_top if channel == "top" else ev.raw_bot).astype(np.float64)
                t = ev.raw_t_us.astype(np.float64)
                bw = min(100, sig.size)
                baseline = float(np.mean(sig[:bw]))
                atten = np.maximum(sig - baseline, 0.0)
                t_rel_ms = (t - ev.t_trigger_us) / 1000.0
                ax.plot(t_rel_ms, atten, color=col, alpha=0.55, linewidth=0.8,
                        label=pos if j == 0 else None)
        ax.set_xlabel("t − t_trigger (ms)")
        ax.set_ylabel(f"{channel.upper()} beam occlusion (ADC counts above baseline)")
        ax.set_title(f"{channel.upper()} beam")
        ax.grid(alpha=0.3)
        ax.legend(loc="upper right", fontsize=8)
        ax.axvline(0.0, color="green", linestyle="--", alpha=0.4, linewidth=1)

    fig.tight_layout()
    out_path = out_dir / "raw_overlays_all_positions.png"
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"  composite -> {out_path}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_ROOT.exists():
        sys.exit(f"No data dir: {DATA_ROOT}")
    if not TODAY_POSITION_MAP:
        # Discover automatically: every *_uart.log file is one capture.
        log_files = sorted(list(DATA_ROOT.glob("*_uart.log")) + list(DATA_ROOT.glob("*.uart.log")))
        if not log_files:
            sys.exit(f"No captures in {DATA_ROOT} yet. Run after the bench session.")
        print(f"Discovered {len(log_files)} capture(s). Using filename stems as position tags.")
        per_position_events = {}
        for log in log_files:
            stem = log.stem.replace("_uart", "").replace(".uart", "")
            events = parse_uart_log(log, position_tag=stem)
            raw_n = sum(1 for e in events if e.has_raw)
            print(f"  {stem}: {len(events)} drops, {raw_n} with raw waveform")
            if raw_n > 0:
                per_position_events[stem] = events
    else:
        per_position_events = {}
        for stem, position_tag in TODAY_POSITION_MAP.items():
            log = DATA_ROOT / f"{stem}.uart.log"
            if not log.exists():
                continue
            events = parse_uart_log(log, position_tag=position_tag)
            if any(e.has_raw for e in events):
                per_position_events.setdefault(position_tag, []).extend(events)

    if not per_position_events:
        sys.exit("No captures with raw waveform data — make sure firmware was flashed with ENABLE_RAW_CAPTURE=1.")

    print(f"\nPlotting per-position overlays:")
    for pos, evs in per_position_events.items():
        plot_one_position(pos, evs, OUT_DIR)

    print(f"\nPlotting composite:")
    plot_composite(per_position_events, OUT_DIR)


if __name__ == "__main__":
    main()
