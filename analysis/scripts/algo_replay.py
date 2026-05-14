"""Offline algorithm replay harness — Phase 2 of the 2026-05-14 PM bench session.

The bench session captures per-drop raw beam waveforms (TOP/BOT photodiode
ADC samples) emitted via the firmware UART path:

    DROP_RAW_BEGIN,<t_ms>,<drop_N>,<sample_count>,<t_first_us>,<t_last_us>,<t_trigger_us>
    RAW,<t_us>,<top_adc>,<bot_adc>       x sample_count
    DROP_RAW_END,<drop_N>

This module parses those windows out of a UART log, optionally pairs them
with gravimetric scale data, and runs an algorithm function across all
drops to produce per-position K-fit metrics. The point is that ONE bench
capture supports unlimited offline algorithm iterations — no flash cycles
between candidates.

Algorithm signature contract:

    def algo(event: DropEvent, **params) -> AlgoResult

where AlgoResult carries the volume estimate, a quality flag (to reject
contaminated drops without polluting the K-fit), and arbitrary debug info.

Methodology and dataset description: data/raw/2026-05-14_pm/README.md.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
import pandas as pd


# --- Data model ---------------------------------------------------------

@dataclass
class DropEvent:
    """One drop's complete record: edge timestamps, raw waveform, labels."""
    drop_n: int
    t_ms: int

    # Edge-time data — matches the existing DROP CSV schema.
    transit_us: int          # tB_in - tT_in
    pulse_top_us: int        # tT_out - tT_in
    pulse_bot_us: int        # tB_out - tB_in
    top_raw_at_in: int       # ADC at tT_in
    bot_raw_at_in: int       # ADC at tB_in

    # Raw waveform — present iff a DROP_RAW_BEGIN/END pair followed the
    # DROP row in the UART log. Empty arrays if the firmware build lacks
    # ENABLE_RAW_CAPTURE or this drop's dump was missed.
    raw_t_us: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.uint32))
    raw_top: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.uint16))
    raw_bot: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.uint16))
    t_trigger_us: int = 0   # TIM2 µs at tT_in (the trigger anchor)

    # Run-level labels — set by the loader from filename/path conventions.
    position_tag: str = ""   # e.g. "P1_high", "P3_umbilical"
    flow_mlh: float = float("nan")

    @property
    def has_raw(self) -> bool:
        return self.raw_top.size > 0

    @property
    def sample_period_us_estimate(self) -> float:
        """Mean sample period across the raw window, for sanity checks."""
        if self.raw_t_us.size < 2:
            return float("nan")
        return float(np.mean(np.diff(self.raw_t_us)))


@dataclass
class AlgoResult:
    """One algorithm's per-drop output."""
    volume_uL: float
    quality_ok: bool = True          # False -> drop excluded from K-fit + metrics
    debug: dict = field(default_factory=dict)


# --- UART log parser ---------------------------------------------------

_RE_DROP = re.compile(
    r"^DROP,(\d+),(\d+),(\d+),(\d+),(\d+),(-?\d+),(-?\d+),(-?\d+),(\d+),(-?\d+),(\d+),(\d+)$"
)
_RE_DROP_RAW_BEGIN = re.compile(
    r"^DROP_RAW_BEGIN,(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)$"
)
_RE_DROP_RAW_END = re.compile(r"^DROP_RAW_END,(\d+)$")
_RE_RAW = re.compile(r"^RAW,(\d+),(\d+),(\d+)$")


def parse_uart_log(path: str | Path,
                   position_tag: str = "",
                   flow_mlh: float = float("nan")) -> list[DropEvent]:
    """Parse a firmware UART log into a list of DropEvent.

    The DROP row precedes the DROP_RAW_BEGIN block for the same drop_N
    (firmware emits log_drop_csv before dump_raw_window). We pair them
    by drop_N.
    """
    events_by_drop_n: dict[int, DropEvent] = {}
    raw_accum_drop_n: int | None = None
    raw_accum_t: list[int] = []
    raw_accum_top: list[int] = []
    raw_accum_bot: list[int] = []
    raw_accum_trigger_us = 0

    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # The bench UART logger (tools/log_uart_run.py) prepends a
        # wall-clock float + tab before each firmware line. Strip if present.
        if "\t" in line:
            ts_part, _, rest = line.partition("\t")
            try:
                float(ts_part)
                line = rest
            except ValueError:
                pass

        m = _RE_DROP.match(line)
        if m:
            t_ms, drop_n, transit_us, pulse_top_us, pulse_bot_us, v_c, d_t, V_t, state, Q_c, top_raw, bot_raw = m.groups()
            drop_n = int(drop_n)
            if drop_n == 0:
                continue  # SIM_DROP synthetic event — skip
            events_by_drop_n[drop_n] = DropEvent(
                drop_n=drop_n,
                t_ms=int(t_ms),
                transit_us=int(transit_us),
                pulse_top_us=int(pulse_top_us),
                pulse_bot_us=int(pulse_bot_us),
                top_raw_at_in=int(top_raw),
                bot_raw_at_in=int(bot_raw),
                position_tag=position_tag,
                flow_mlh=flow_mlh,
            )
            continue

        m = _RE_DROP_RAW_BEGIN.match(line)
        if m:
            t_ms, drop_n, sample_count, t_first_us, t_last_us, t_trigger_us = m.groups()
            raw_accum_drop_n = int(drop_n)
            raw_accum_t = []
            raw_accum_top = []
            raw_accum_bot = []
            raw_accum_trigger_us = int(t_trigger_us)
            continue

        m = _RE_RAW.match(line)
        if m and raw_accum_drop_n is not None:
            t_us, top, bot = m.groups()
            raw_accum_t.append(int(t_us))
            raw_accum_top.append(int(top))
            raw_accum_bot.append(int(bot))
            continue

        m = _RE_DROP_RAW_END.match(line)
        if m and raw_accum_drop_n is not None:
            ev = events_by_drop_n.get(raw_accum_drop_n)
            if ev is not None:
                ev.raw_t_us = np.array(raw_accum_t, dtype=np.uint32)
                ev.raw_top = np.array(raw_accum_top, dtype=np.uint16)
                ev.raw_bot = np.array(raw_accum_bot, dtype=np.uint16)
                ev.t_trigger_us = raw_accum_trigger_us
            raw_accum_drop_n = None

    return [events_by_drop_n[k] for k in sorted(events_by_drop_n.keys())]


# --- Gravimetric pairing ----------------------------------------------

def pair_with_gravimetric(events: list[DropEvent],
                          scale_csv_path: str | Path) -> dict[str, float]:
    """Compute run-level ground truth from a Mettler-Toledo scale CSV.

    Per `docs/limitations.md` §2 (Two-orifice divergence), we DO NOT
    attempt per-drop pairing. Returns run-level numbers:

        V_true_per_drop_uL = (mass_end - mass_start) / drop_count_chamber
    """
    df = pd.read_csv(scale_csv_path)
    # The Mettler scale CSV typically has time_s, mass_g columns; adjust
    # the column lookup if the bench logger uses different names.
    mass_col = next((c for c in df.columns if "mass" in c.lower() or "g" in c.lower()[:2]), None)
    if mass_col is None:
        raise ValueError(f"{scale_csv_path}: no mass column found in {df.columns.tolist()}")
    mass_g = pd.to_numeric(df[mass_col], errors="coerce").dropna()
    delta_mL = float(mass_g.iloc[-1] - mass_g.iloc[0])  # 1 g ≈ 1 mL for saline
    return {
        "drop_count_uart": len(events),
        "scale_delta_mL": delta_mL,
        "V_true_per_drop_uL": (delta_mL * 1000.0 / len(events)) if events else float("nan"),
    }


# --- Algorithm reference (firmware replay, sanity check) -------------

BEAM_PITCH_MM = 10.0
G_MMPS2 = 9810.0
BEAM_WIDTH_MM = 0.0
V_CAL_K = 1.27


def algo_reference(event: DropEvent) -> AlgoResult:
    """Bit-near-exact replica of firmware drop-volume math (main.c §794).

    Use this to sanity-check the harness: re-running it across yesterday's
    edge-time data should reproduce the firmware-emitted drop_volume_uL.
    """
    dt_us = event.transit_us
    pulse_mean_us = (event.pulse_top_us + event.pulse_bot_us) // 2
    if dt_us <= 500 or pulse_mean_us <= 100:
        return AlgoResult(volume_uL=0.0, quality_ok=False, debug={"reason": "fast"})

    dt_s = dt_us * 1e-6
    tau_s = pulse_mean_us * 1e-6
    v_mmps = BEAM_PITCH_MM / dt_s - 0.5 * G_MMPS2 * dt_s
    chord_mm = v_mmps * tau_s + 0.5 * G_MMPS2 * tau_s ** 2
    d_mm = chord_mm - BEAM_WIDTH_MM
    vol_uL = (math.pi / 6.0) * d_mm ** 3 * V_CAL_K

    quality_ok = (v_mmps >= 50.0) and (d_mm >= 0.1) and (0.0 < vol_uL <= 500.0)
    return AlgoResult(
        volume_uL=vol_uL,
        quality_ok=quality_ok,
        debug={"v_mmps": v_mmps, "d_mm": d_mm, "tau_s": tau_s, "dt_s": dt_s},
    )


# --- Evaluate ---------------------------------------------------------

def evaluate(algo: Callable[[DropEvent], AlgoResult],
             events: list[DropEvent],
             v_true_per_position: dict[str, float]) -> dict:
    """Run `algo` over `events`, fit a per-position K, report metrics.

    Per-position K is the scalar that makes the algorithm's mean volume
    match the gravimetric truth at that position. K_max/K_min across
    positions is the headline number (matches §17's framing).
    """
    rows = []
    for ev in events:
        result = algo(ev)
        rows.append({
            "drop_n": ev.drop_n,
            "position_tag": ev.position_tag,
            "flow_mlh": ev.flow_mlh,
            "V_est_uL": result.volume_uL,
            "quality_ok": result.quality_ok,
        })
    df = pd.DataFrame(rows)
    df_ok = df[df["quality_ok"]]
    rejected_pct = 100.0 * (1.0 - len(df_ok) / max(len(df), 1))

    per_pos = []
    for pos, grp in df_ok.groupby("position_tag"):
        V_est_mean = grp["V_est_uL"].mean()
        V_true = v_true_per_position.get(pos, float("nan"))
        K_fit = V_true / V_est_mean if V_est_mean else float("nan")
        per_pos.append({
            "position_tag": pos,
            "n_drops": len(grp),
            "V_est_mean_uL": V_est_mean,
            "V_true_uL": V_true,
            "K_fit": K_fit,
        })
    per_pos_df = pd.DataFrame(per_pos)

    K_vals = per_pos_df["K_fit"].dropna().values
    return {
        "rejected_pct": rejected_pct,
        "per_position": per_pos_df,
        "K_min": float(np.min(K_vals)) if K_vals.size else float("nan"),
        "K_max": float(np.max(K_vals)) if K_vals.size else float("nan"),
        "K_ratio": float(np.max(K_vals) / np.min(K_vals)) if K_vals.size and np.min(K_vals) > 0 else float("nan"),
    }


# --- CLI sanity check -------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(
            "usage: algo_replay.py <uart.log> [position_tag] [flow_mlh]\n"
            "  Parses one UART log and prints a summary of parsed events\n"
            "  plus the reference-replay K fit (if no gravimetric pairing,\n"
            "  V_true is omitted and only counts are shown)."
        )
        sys.exit(0)
    log_path = sys.argv[1]
    pos = sys.argv[2] if len(sys.argv) > 2 else "unknown"
    flow = float(sys.argv[3]) if len(sys.argv) > 3 else float("nan")

    events = parse_uart_log(log_path, position_tag=pos, flow_mlh=flow)
    print(f"Parsed {len(events)} DROP events from {log_path}")
    raw_count = sum(1 for e in events if e.has_raw)
    print(f"  with raw waveform: {raw_count} / {len(events)}")
    if raw_count > 0:
        sample_periods = [e.sample_period_us_estimate for e in events if e.has_raw]
        print(f"  mean sample period: {np.mean(sample_periods):.2f} µs "
              f"(stdev {np.std(sample_periods):.2f} µs)")
        sample_counts = [e.raw_top.size for e in events if e.has_raw]
        print(f"  samples/window: min={min(sample_counts)} max={max(sample_counts)} "
              f"mean={np.mean(sample_counts):.0f}")

    # Reference replay sanity check — no gravimetric pairing, just print
    # the K-free volume distribution.
    rows = [algo_reference(e).volume_uL for e in events]
    if rows:
        rows_arr = np.array(rows)
        print(f"\nReference-replay V_est (firmware math, K={V_CAL_K}):")
        print(f"  n={len(rows_arr)}  mean={rows_arr.mean():.2f} µL  "
              f"stdev={rows_arr.std():.2f}  CV={rows_arr.std()/rows_arr.mean():.2%}")
