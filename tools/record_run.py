#!/usr/bin/env python3
"""Single-command orchestrator for one EXP-3 bench run.

Chains: tare scale -> UART capture for N seconds -> stable-weight read
-> append row to data/gravimetric_log.csv. Prompts the operator for the
physical steps that can't be automated (placing the vessel, opening
and closing the clamp).

Usage:
  python tools/record_run.py --rate 50 --run V_50_01 --duration 300

Defaults assume COM3 = Dripito UART, COM4 = Mettler-Toledo balance.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from datetime import date as _date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GRAV_LOG = REPO_ROOT / "data" / "gravimetric_log.csv"
GRAV_HEADER = [
    "run_id", "csv_filename", "flow_rate_target_mlh",
    "gravimetric_mass_g", "run_duration_s",
    "drop_count_device", "notes",
]


def _pause(msg: str) -> None:
    try:
        input(f"\n  {msg}  [Enter to continue, Ctrl+C to abort] ")
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(130)


def _confirm(msg: str, default_yes: bool = True) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    try:
        raw = input(f"  {msg} {suffix} ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(130)
    if not raw:
        return default_yes
    return raw.startswith("y")


def _stable_weight(scale_port: str, baud: int, max_wait: float) -> float:
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from log_scale import _open, _send_recv, _parse_weight  # type: ignore
    ser = _open(scale_port, baud, timeout=0.5)
    try:
        line = _send_recv(ser, "S", max_wait_s=max_wait)
        status, grams, raw = _parse_weight(line)
        if grams is None:
            raise RuntimeError(f"status={status} raw={raw!r}")
        return grams
    finally:
        ser.close()


def _tare(scale_port: str, baud: int) -> float:
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from log_scale import _open, _send_recv, _parse_weight  # type: ignore
    ser = _open(scale_port, baud, timeout=0.5)
    try:
        line = _send_recv(ser, "T", max_wait_s=10.0)
        status, grams, raw = _parse_weight(line)
        if status != "S":
            raise RuntimeError(f"tare not stable: status={status} raw={raw!r}")
        return grams
    finally:
        ser.close()


def _count_drops(csv_path: Path) -> int:
    with csv_path.open(encoding="utf-8") as f:
        return sum(1 for _ in f) - 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rate", type=int, required=True, choices=(20, 50, 100))
    ap.add_argument("--run", required=True, help="run id (e.g. V_50_01)")
    ap.add_argument("--duration", type=float, default=300.0,
                    help="UART capture duration in seconds (default 300)")
    ap.add_argument("--uart-port", default="COM3")
    ap.add_argument("--uart-baud", type=int, default=115200)
    ap.add_argument("--scale-port", default="COM4")
    ap.add_argument("--scale-baud", type=int, default=9600)
    ap.add_argument("--scale-max-wait", type=float, default=30.0,
                    help="seconds to wait for stable weight after run")
    ap.add_argument("--board", default="1")
    ap.add_argument("--date", default=None)
    ap.add_argument("--notes", default="")
    ap.add_argument("--saline-density-g-ml", type=float, default=1.005,
                    help="density used for gravimetric flow sanity check")
    args = ap.parse_args(argv)

    date_iso = args.date or _date.today().isoformat()
    run_idx = args.run.split("_")[-1] if "_" in args.run else args.run
    csv_name = (
        f"{date_iso}_macro20_{args.rate}mlh_{run_idx}_board{args.board}.csv"
    )
    csv_path = REPO_ROOT / "data" / "raw" / csv_name

    if csv_path.exists():
        print(f"ERROR: {csv_path.relative_to(REPO_ROOT)} exists already.",
              file=sys.stderr)
        return 2

    print(f"\n=== Bench run {args.run}  ({args.rate} mL/hr, {args.duration:.0f} s) ===")
    print(f"  UART:  {args.uart_port}  ->  data/raw/{csv_name}")
    print(f"  Scale: {args.scale_port}")

    _pause("Place empty vessel on scale; verify drip set + chamber mount")
    print("  Taring scale...")
    try:
        zero = _tare(args.scale_port, args.scale_baud)
        print(f"  tare OK (zero {zero:+.4f} g)")
    except RuntimeError as e:
        print(f"  ERROR: tare failed: {e}", file=sys.stderr)
        return 2

    _pause("Open clamp; wait for steady drip rate")

    print("\n  Starting UART capture...")
    cmd = [
        sys.executable, str(REPO_ROOT / "tools" / "log_uart_run.py"),
        "capture",
        "--port", args.uart_port,
        "--baud", str(args.uart_baud),
        "--rate", str(args.rate),
        "--run", args.run,
        "--duration", f"{args.duration:.0f}",
        "--date", date_iso,
        "--board", args.board,
    ]
    rc = subprocess.call(cmd)
    if rc != 0:
        print(f"  ERROR: UART capture exited {rc}", file=sys.stderr)
        return rc

    if not csv_path.exists():
        print(f"  ERROR: expected CSV {csv_path} not written", file=sys.stderr)
        return 2

    drop_count = _count_drops(csv_path)
    print(f"\n  Drops captured: {drop_count}")
    if drop_count == 0:
        if not _confirm("No drops captured. Log this run anyway?", default_yes=False):
            print("  Aborted. CSV kept for inspection; no gravimetric row written.")
            return 1

    _pause("Close clamp; wait for scale to settle")
    print(f"\n  Reading stable mass (max wait {args.scale_max_wait:.0f} s)...")
    try:
        grams = _stable_weight(args.scale_port, args.scale_baud,
                               args.scale_max_wait)
    except RuntimeError as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return 2
    print(f"  Mass: {grams:.4f} g")

    row = {
        "run_id": args.run,
        "csv_filename": csv_name,
        "flow_rate_target_mlh": args.rate,
        "gravimetric_mass_g": f"{grams:.4f}",
        "run_duration_s": f"{args.duration:.1f}",
        "drop_count_device": drop_count,
        "notes": args.notes,
    }
    write_header = not GRAV_LOG.exists()
    GRAV_LOG.parent.mkdir(parents=True, exist_ok=True)
    with GRAV_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=GRAV_HEADER)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    grav_flow = (grams / args.saline_density_g_ml) / (args.duration / 3600.0)
    pct_err = (grav_flow - args.rate) / args.rate * 100
    print(f"\n  Gravimetric flow: {grav_flow:.2f} mL/hr "
          f"({pct_err:+.1f}% vs target {args.rate})")
    if abs(pct_err) > 30:
        print("  WARNING: >30% off target. Check clamp setting / settling time.")

    print(f"\n  Logged to {GRAV_LOG.relative_to(REPO_ROOT)}")
    print("=== run complete ===\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
