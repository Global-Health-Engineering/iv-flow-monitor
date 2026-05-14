#!/usr/bin/env python3
"""Read the live debug log over SWD from a running Dripito Rev-B board.

Firmware writes to a ring buffer in RAM (struct dbg_log_t in main.c). This
script attaches to ST-Link in Hot-plug mode (no CPU halt, no reset) via
STM32_Programmer_CLI, snapshots the buffer, and emits any new entries.

Usage:
    python read_swd_log.py            # snapshot once, print new entries, exit
    python read_swd_log.py --follow   # poll forever (~3 Hz)
    python read_swd_log.py --all      # print all 32 slots regardless of head
"""

import argparse
import json
import os
import re
import struct
import subprocess
import sys
import time

PROG_CLI = r"C:\ST\STM32CubeIDE_1.18.1\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.2.100.202412061334\tools\bin\STM32_Programmer_CLI.exe"

LOG_ADDR     = 0x20000008      # symbol `dbg_log` from arm-none-eabi-nm
LOG_SLOTS    = 32
LOG_SLOT_B   = 48
LOG_TOTAL_B  = 4 + 4 + LOG_SLOTS * LOG_SLOT_B
LOG_TOTAL_W  = (LOG_TOTAL_B + 3) // 4

MAGIC = 0xD11D0001

STATE_FILE = os.path.join(os.path.dirname(__file__), ".read_swd_log_state.json")

HEX_LINE = re.compile(
    r"^0x([0-9A-Fa-f]{8})\s*:\s*((?:[0-9A-Fa-f]{8}\s*)+)$"
)


def read_words(addr_hex, n_words):
    """Invoke STM32_Programmer_CLI Hotplug read; return list of 32-bit words.
    -r32 takes a byte count, not a word count, despite the flag name."""
    n_bytes = n_words * 4
    cmd = [PROG_CLI, "-c", "port=SWD", "mode=Hotplug",
           "-r32", addr_hex, str(n_bytes)]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    words = []
    for line in out.stdout.splitlines():
        m = HEX_LINE.match(line.strip())
        if not m:
            continue
        for w in m.group(2).split():
            words.append(int(w, 16))
    return words[:n_words]


def decode_log(words):
    """words is the raw 386-word read starting at dbg_log. Returns
       (magic, head, [slot_strings])."""
    raw = b"".join(struct.pack("<I", w) for w in words)
    magic, head = struct.unpack("<II", raw[:8])
    slots = []
    for s in range(LOG_SLOTS):
        off = 8 + s * LOG_SLOT_B
        chunk = raw[off:off + LOG_SLOT_B]
        nul = chunk.find(b"\x00")
        if nul < 0:
            nul = LOG_SLOT_B
        try:
            slots.append(chunk[:nul].decode("ascii", errors="replace"))
        except Exception:
            slots.append(repr(chunk[:nul]))
    return magic, head, slots


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_head": 0}


def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


def snapshot(args, state):
    try:
        words = read_words(f"0x{LOG_ADDR:08X}", LOG_TOTAL_W)
    except subprocess.TimeoutExpired:
        print("[!] SWD read timed out", file=sys.stderr)
        return state
    if len(words) < LOG_TOTAL_W:
        print(f"[!] Short read: got {len(words)} words, expected {LOG_TOTAL_W}",
              file=sys.stderr)
        return state

    magic, head, slots = decode_log(words)
    if magic != MAGIC:
        print(f"[!] Magic mismatch: 0x{magic:08X} (expected 0x{MAGIC:08X}) — "
              "wrong address or firmware not running our build?", file=sys.stderr)
        return state

    if args.all:
        last = max(0, head - LOG_SLOTS)
        end  = head
    else:
        last = state.get("last_head", 0)
        if last > head:
            # Device rebooted; start from 0.
            last = 0
        end = head

    if end > last:
        start = max(last, end - LOG_SLOTS)  # avoid replaying overwritten slots
        if start > last:
            print(f"[!] Lost {start - last} entries (overrun: read too slow)",
                  file=sys.stderr)
        for i in range(start, end):
            slot_idx = i % LOG_SLOTS
            print(f"{i:6d}  {slots[slot_idx]}")
        sys.stdout.flush()

    state["last_head"] = end
    return state


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--follow", action="store_true", help="poll continuously")
    p.add_argument("--all", action="store_true",
                   help="print all 32 slots regardless of last-read head")
    p.add_argument("--interval", type=float, default=0.4,
                   help="poll interval in seconds (default 0.4)")
    args = p.parse_args()

    state = load_state()
    if args.follow:
        try:
            while True:
                state = snapshot(args, state)
                save_state(state)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n(stopped)", file=sys.stderr)
    else:
        state = snapshot(args, state)
        save_state(state)


if __name__ == "__main__":
    main()
