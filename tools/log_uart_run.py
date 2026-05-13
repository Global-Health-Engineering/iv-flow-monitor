#!/usr/bin/env python3
"""Capture or convert Dripito Rev-B UART output into per-run CSVs.

Firmware v1 line conventions (see firmware/.../main.c print routines):

  # ...                       boot preamble comment lines
  DROP,<t_ms>,<drop_N>,<transit_us>,<pulse_top_us>,<pulse_bot_us>,
       <v_cmps>,<d_0.1mm>,<V_0.1uL>,<state>,<Q_cmLph>,<top_raw>,<bot_raw>
  EVT,<t_ms>,<message>        events (BOOT, DROP_REJECT, ...)
  <...                        RX command responses

The script keeps the full UART stream verbatim in a .log mirror and
emits a per-run CSV containing only DROP rows (without the "DROP,"
prefix), matching the schema required by analysis/scripts/load_run.py.

Subcommands:
  capture    Read live from a COM port; write CSV + .log to data/raw/.
  convert    Parse an existing .log into one or more CSVs.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from datetime import date as _date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = REPO_ROOT / "data" / "raw"

CSV_HEADER = [
    "abs_ms", "drop_N",
    "transit_us", "pulse_top_us", "pulse_bot_us",
    "v_cmps", "d_0.1mm", "V_0.1uL",
    "state", "Q_cmLph",
    "top_raw", "bot_raw",
]

EVT_BOOT_RE = re.compile(r"^EVT,\d+,BOOT")


def _default_csv_name(date_iso: str, rate_mlh: int, run_idx: str, board: str) -> str:
    return f"{date_iso}_macro20_{rate_mlh}mlh_{run_idx}_board{board}.csv"


def _open_csv(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    f = path.open("w", newline="", encoding="utf-8")
    w = csv.writer(f)
    w.writerow(CSV_HEADER)
    return f, w


def _parse_drop(line: str) -> list[str] | None:
    """Return the 12 data fields if `line` is a well-formed DROP row."""
    parts = line.strip().split(",")
    if len(parts) != 13 or parts[0] != "DROP":
        return None
    body = parts[1:]
    try:
        for v in body:
            int(v)
    except ValueError:
        return None
    return body


def _normalise_run_idx(run: str) -> str:
    """`V_50_01` -> `01`; `01` -> `01`."""
    return run.split("_")[-1] if "_" in run else run


def cmd_capture(args: argparse.Namespace) -> int:
    import serial  # pyserial; lazy import so convert/--help work without it
    from serial.tools import list_ports

    date_iso = args.date or _date.today().isoformat()
    run_idx = _normalise_run_idx(args.run)
    csv_name = args.csv or _default_csv_name(date_iso, args.rate, run_idx, args.board)
    out_dir = Path(args.out_dir).resolve()
    csv_path = out_dir / csv_name
    log_path = csv_path.with_suffix(".log")

    if csv_path.exists() and not args.force:
        print(f"ERROR: {csv_path.name} exists. --force to overwrite.",
              file=sys.stderr)
        return 2

    print("Visible ports:")
    for p in list_ports.comports():
        marker = "  <-- selected" if p.device == args.port else ""
        print(f"  {p.device}\t{p.description}\t{p.hwid}{marker}")
    print()
    print(f"Port:     {args.port} @ {args.baud} 8N1")
    print(f"Run:      {args.run} ({args.rate} mL/hr)")
    print(f"CSV:      {csv_path}")
    print(f"Log:      {log_path}")
    dur_label = f"{args.duration:.0f} s" if args.duration else "open-ended (Ctrl+C to stop)"
    print(f"Duration: {dur_label}")
    print()

    ser = serial.Serial(args.port, args.baud, timeout=0.2)
    csv_f, csv_w = _open_csv(csv_path)
    log_f = log_path.open("w", encoding="utf-8")

    t_start = time.monotonic()
    drop_count = 0
    line_count = 0
    try:
        while True:
            if args.duration and (time.monotonic() - t_start) >= args.duration:
                print(f"\n[duration {args.duration:.0f} s reached]")
                break
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if not line:
                continue
            line_count += 1
            log_f.write(line + "\n")
            log_f.flush()
            fields = _parse_drop(line)
            if fields is not None:
                csv_w.writerow(fields)
                csv_f.flush()
                drop_count += 1
                if drop_count % 5 == 0:
                    elapsed = time.monotonic() - t_start
                    print(f"  drop {drop_count}  (t={elapsed:5.1f} s)")
    except KeyboardInterrupt:
        print("\n[interrupted]")
    finally:
        csv_f.close()
        log_f.close()
        ser.close()

    print()
    print(f"  Captured: {drop_count} drops, {line_count} total UART lines")
    print(f"  CSV:  {csv_path.relative_to(REPO_ROOT)}")
    print(f"  Log:  {log_path.relative_to(REPO_ROOT)}")
    if drop_count == 0:
        print("  WARNING: no DROP rows captured. Check device state, "
              "fluid path, and that COM3 is the Dripito (not the scale).")
    return 0


def cmd_convert(args: argparse.Namespace) -> int:
    src = Path(args.log).resolve()
    if not src.exists():
        print(f"ERROR: {src} not found", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    date_iso = args.date or _date.today().isoformat()
    base_run_idx = _normalise_run_idx(args.run)

    segments: list[list[list[str]]] = [[]]
    for line in src.read_text(encoding="utf-8", errors="replace").splitlines():
        if args.split_on_evt_reset and EVT_BOOT_RE.match(line) and segments[-1]:
            segments.append([])
        fields = _parse_drop(line)
        if fields is not None:
            segments[-1].append(fields)
    segments = [s for s in segments if s]
    if not segments:
        print(f"  No DROP lines in {src.name}", file=sys.stderr)
        return 1

    written = 0
    for idx, seg in enumerate(segments, start=1):
        run_idx = f"{base_run_idx}-{idx}" if len(segments) > 1 else base_run_idx
        csv_name = args.csv or _default_csv_name(date_iso, args.rate, run_idx, args.board)
        csv_path = out_dir / csv_name
        if csv_path.exists() and not args.force:
            print(f"  SKIP {csv_path.name} (exists; --force to overwrite)")
            continue
        f, w = _open_csv(csv_path)
        try:
            for row in seg:
                w.writerow(row)
        finally:
            f.close()
        print(f"  Wrote {csv_path.relative_to(REPO_ROOT)} ({len(seg)} drops)")
        written += 1
    return 0 if written else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("capture", help="live capture from a COM port")
    c.add_argument("--port", required=True, help="serial port (e.g. COM3)")
    c.add_argument("--baud", type=int, default=115200)
    c.add_argument("--rate", type=int, required=True, choices=(20, 50, 100),
                   help="target flow rate (mL/hr)")
    c.add_argument("--run", required=True,
                   help="run id (e.g. V_50_01 or just 01)")
    c.add_argument("--duration", type=float, default=0.0,
                   help="capture duration in seconds (0 = until Ctrl+C)")
    c.add_argument("--date", default=None,
                   help="date for filename (YYYY-MM-DD; default today)")
    c.add_argument("--board", default="1", help="board number for filename")
    c.add_argument("--csv", default=None, help="override output CSV name")
    c.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR),
                   help="output directory (default data/raw/)")
    c.add_argument("--force", action="store_true",
                   help="overwrite existing CSV")
    c.set_defaults(func=cmd_capture)

    v = sub.add_parser("convert", help="convert an existing .log file")
    v.add_argument("log", help="path to UART .log file")
    v.add_argument("--rate", type=int, required=True, choices=(20, 50, 100))
    v.add_argument("--run", required=True)
    v.add_argument("--date", default=None)
    v.add_argument("--board", default="1")
    v.add_argument("--csv", default=None)
    v.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    v.add_argument("--force", action="store_true")
    v.add_argument("--split-on-evt-reset", action="store_true",
                   help="split into multiple CSVs at every EVT,...,BOOT line")
    v.set_defaults(func=cmd_convert)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
