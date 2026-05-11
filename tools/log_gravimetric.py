#!/usr/bin/env python3
"""Bench-side gravimetric logger.

Appends one row to data/gravimetric_log.csv per EXP-3 run.
Run from repo root: `python tools/log_gravimetric.py`.

The tool:
  - Suggests the next run_id by scanning the existing log
  - Validates inputs (mass > 0, duration > 0, drop_count > 0 integer)
  - Refuses to overwrite an existing run_id (use --force to override)
  - Echoes the computed gravimetric flow rate as a sanity check
  - Writes the header row if the log doesn't exist yet
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "data" / "gravimetric_log.csv"

HEADER = [
    "run_id",
    "csv_filename",
    "flow_rate_target_mlh",
    "gravimetric_mass_g",
    "run_duration_s",
    "drop_count_device",
    "notes",
]


def load_existing() -> list[dict[str, str]]:
    if not LOG_PATH.exists():
        return []
    with LOG_PATH.open(newline="") as f:
        return list(csv.DictReader(f))


def suggest_next_run_id(existing: list[dict[str, str]], rate_mlh: int) -> str:
    pattern = re.compile(rf"^V_{rate_mlh}_(\d+)$")
    used = [int(m.group(1)) for row in existing if (m := pattern.match(row["run_id"]))]
    return f"V_{rate_mlh}_{(max(used) + 1) if used else 1:02d}"


def prompt(label: str, default: str | None = None, cast=str, validate=None) -> object:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{label}{suffix}: ").strip()
        if not raw and default is not None:
            raw = default
        if not raw:
            print("  (required)")
            continue
        try:
            value = cast(raw)
        except (ValueError, TypeError) as e:
            print(f"  invalid: {e}")
            continue
        if validate and not validate(value):
            print("  validation failed")
            continue
        return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="overwrite an existing run_id")
    args = parser.parse_args()

    existing = load_existing()
    existing_ids = {row["run_id"] for row in existing}

    print(f"\nLog: {LOG_PATH.relative_to(REPO_ROOT)}  ({len(existing)} runs so far)\n")

    flow_rate = prompt(
        "Flow rate target (mL/hr)",
        cast=int,
        validate=lambda v: v in (20, 50, 100),
    )
    default_run_id = suggest_next_run_id(existing, flow_rate)
    run_id = prompt("Run ID", default=default_run_id)

    if run_id in existing_ids and not args.force:
        print(f"\n  ERROR: '{run_id}' already in log. Re-run with --force to overwrite.")
        return 1

    default_csv = f"{prompt('Date (YYYY-MM-DD)', cast=str)}_macro20_{flow_rate}mlh_{run_id.split('_')[-1]}_board1.csv"
    csv_filename = prompt("CSV filename", default=default_csv)
    mass_g = prompt("Gravimetric mass (g)", cast=float, validate=lambda v: v > 0)
    duration_s = prompt("Run duration (s)", default="300", cast=float, validate=lambda v: v > 0)
    drop_count = prompt("Device drop count", cast=int, validate=lambda v: v > 0)
    notes = input("Notes (optional): ").strip()

    # Sanity check: flow rate from gravimetric
    grav_flow = (mass_g / 1.005) / (duration_s / 3600)
    pct_err = (grav_flow - flow_rate) / flow_rate * 100
    print(f"\n  Gravimetric flow: {grav_flow:.2f} mL/hr  ({pct_err:+.1f}% vs target {flow_rate})")
    if abs(pct_err) > 30:
        print("  WARNING: >30% off target. Check scale tare and roller-clamp setting.")

    row = {
        "run_id": run_id,
        "csv_filename": csv_filename,
        "flow_rate_target_mlh": flow_rate,
        "gravimetric_mass_g": f"{mass_g:.4f}",
        "run_duration_s": f"{duration_s:.1f}",
        "drop_count_device": drop_count,
        "notes": notes,
    }

    file_exists = LOG_PATH.exists()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if args.force and run_id in existing_ids:
        rows = [r for r in existing if r["run_id"] != run_id] + [row]
        with LOG_PATH.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=HEADER)
            writer.writeheader()
            writer.writerows(rows)
    else:
        with LOG_PATH.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=HEADER)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    print(f"\n  Logged: {run_id}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
