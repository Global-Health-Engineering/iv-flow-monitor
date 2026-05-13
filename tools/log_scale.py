#!/usr/bin/env python3
"""Talk SICS to a Mettler-Toledo balance over a USB CDC virtual COM port.

NewClassic MS-series balances enumerate as USB CDC (VID 0x0EB8) and
respond to the Standard Interface Command Set (SICS). Subset used here:

  I3   identify balance: model, serial, firmware version
  S    send weight once stable (blocks until stable)
  SI   send weight immediately (stable or not)
  Z    zero  (only if pan is empty)
  T    tare  (set current weight as new zero)

Line termination is CR LF in both directions. Default baud is 9600 8N1
but CDC links are baud-rate-agnostic so any value works.

Subcommands:
  probe   identify and read immediate weight (sanity check)
  weigh   read a stable weight; print "<grams>" to stdout for shell use
  tare    set current weight as new zero
  zero    zero the balance (empty pan required)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def _open(port: str, baud: int, timeout: float):
    import serial  # pyserial; lazy import for --help
    return serial.Serial(port, baud, timeout=timeout)


def _send_recv(ser, cmd: str, max_wait_s: float = 5.0) -> str:
    """Send a SICS command and return the first non-empty response line."""
    ser.reset_input_buffer()
    ser.write((cmd + "\r\n").encode("ascii"))
    ser.flush()
    t0 = time.monotonic()
    buf = bytearray()
    while time.monotonic() - t0 < max_wait_s:
        chunk = ser.read(256)
        if chunk:
            buf.extend(chunk)
            if b"\r\n" in buf:
                line = buf.split(b"\r\n", 1)[0]
                return line.decode("ascii", errors="replace").strip()
        else:
            time.sleep(0.02)
    return ""


def _parse_weight(line: str) -> tuple[str, float | None, str | None]:
    """Parse a SICS weight response. Returns (status, grams, raw).

    Status codes seen on MS-series:
      S  stable
      D  dynamic / unstable
      +  overload
      -  underload
      I  command not executable (range busy, tare in progress)
    """
    tokens = line.split()
    if len(tokens) < 2:
        return ("?", None, line)
    status = tokens[1]
    if status in ("+", "-", "I"):
        return (status, None, line)
    if status not in ("S", "D"):
        return (status, None, line)
    if len(tokens) < 4:
        return (status, None, line)
    try:
        grams = float(tokens[2])
    except ValueError:
        return (status, None, line)
    unit = tokens[3]
    if unit != "g":
        # MS-series defaults to grams; flag others as raw
        return (status, None, line)
    return (status, grams, line)


def cmd_probe(args: argparse.Namespace) -> int:
    ser = _open(args.port, args.baud, timeout=0.5)
    try:
        ident = _send_recv(ser, "I3")
        print(f"I3:  {ident or '(no response)'}")
        si = _send_recv(ser, "SI")
        status, grams, raw = _parse_weight(si)
        if grams is not None:
            stab = "stable" if status == "S" else "dynamic"
            print(f"SI:  {grams:.4f} g ({stab})")
        else:
            print(f"SI:  status={status}  raw={raw!r}")
    finally:
        ser.close()
    return 0


def cmd_weigh(args: argparse.Namespace) -> int:
    ser = _open(args.port, args.baud, timeout=0.5)
    try:
        # S blocks on the balance side until stable
        line = _send_recv(ser, "S", max_wait_s=args.max_wait)
        status, grams, raw = _parse_weight(line)
        if grams is None:
            print(f"ERROR: status={status}  raw={raw!r}", file=sys.stderr)
            return 2
        # Print only the number to stdout so shell-capture is clean
        print(f"{grams:.4f}")
        if args.verbose:
            print(f"  (status={status})", file=sys.stderr)
    finally:
        ser.close()
    return 0


def cmd_tare(args: argparse.Namespace) -> int:
    ser = _open(args.port, args.baud, timeout=0.5)
    try:
        line = _send_recv(ser, "T", max_wait_s=10.0)
        status, grams, raw = _parse_weight(line)
        if status != "S":
            print(f"ERROR: tare not stable; status={status}  raw={raw!r}",
                  file=sys.stderr)
            return 2
        # On success the response carries the new zero point (typically 0.0000)
        print(f"Tare OK (zero point: {grams:.4f} g)")
    finally:
        ser.close()
    return 0


def cmd_zero(args: argparse.Namespace) -> int:
    ser = _open(args.port, args.baud, timeout=0.5)
    try:
        line = _send_recv(ser, "Z", max_wait_s=10.0)
        # Z A = accepted, Z I = pan not empty / out of range
        tokens = line.split()
        if len(tokens) >= 2 and tokens[1] == "A":
            print("Zero OK")
            return 0
        print(f"ERROR: zero rejected. raw={line!r}", file=sys.stderr)
        return 2
    finally:
        ser.close()


def cmd_stream(args: argparse.Namespace) -> int:
    """Stream weights continuously to a CSV using SIR (send immediate, repeat).

    SIR makes the balance push every weight sample (~23 Hz on MS-series) until
    we stop it with @. Output CSV: t_ms,mass_g,status where t_ms is millis
    since stream start and status is 'S' or 'D' per SICS.
    """
    ser = _open(args.port, args.baud, timeout=0.5)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        ser.reset_input_buffer()
        ser.write(b"SIR\r\n")
        ser.flush()
        t0 = time.monotonic()
        deadline = t0 + args.duration
        buf = bytearray()
        n_rows = 0
        with open(out_path, "w", encoding="ascii", newline="") as f:
            f.write("t_ms,mass_g,status\n")
            while time.monotonic() < deadline:
                chunk = ser.read(256)
                if not chunk:
                    continue
                buf.extend(chunk)
                while b"\r\n" in buf:
                    line_bytes, buf = buf.split(b"\r\n", 1)
                    line = line_bytes.decode("ascii", errors="replace").strip()
                    if not line:
                        continue
                    status, grams, _raw = _parse_weight(line)
                    if grams is None:
                        continue
                    t_ms = int((time.monotonic() - t0) * 1000.0)
                    f.write(f"{t_ms},{grams:.4f},{status}\n")
                    n_rows += 1
        # Stop the stream
        try:
            ser.write(b"@\r\n")
            ser.flush()
        except Exception:
            pass
        print(f"Stream complete: {n_rows} rows in {args.duration:.0f} s -> {out_path}")
    finally:
        ser.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--port", default="COM4", help="balance COM port (default COM4)")
    p.add_argument("--baud", type=int, default=9600,
                   help="serial baud (CDC is rate-agnostic; default 9600)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("probe", help="identify balance and read immediate weight"
                   ).set_defaults(func=cmd_probe)

    w = sub.add_parser("weigh", help="read a stable weight to stdout")
    w.add_argument("--max-wait", type=float, default=15.0,
                   help="seconds to wait for stable (default 15)")
    w.add_argument("--verbose", action="store_true")
    w.set_defaults(func=cmd_weigh)

    sub.add_parser("tare", help="set current weight as new zero"
                   ).set_defaults(func=cmd_tare)
    sub.add_parser("zero", help="zero the balance (empty pan required)"
                   ).set_defaults(func=cmd_zero)

    s = sub.add_parser("stream", help="stream weights to CSV via SIR")
    s.add_argument("--duration", type=float, required=True,
                   help="stream duration in seconds")
    s.add_argument("--out", required=True,
                   help="output CSV path (overwritten)")
    s.set_defaults(func=cmd_stream)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
