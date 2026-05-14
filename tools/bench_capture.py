"""Bench-side UART capture for the 2026-05-14 PM session.

Opens COM3 at 115200 (the proven-working baud for this rig's CP210x),
streams all bytes to <out>.uart.log, and prints per-5-sec progress with
DROP/DROP_RAW_BEGIN/DROP_REJECT counters so the operator can tell whether
the firmware is detecting drops in real-time.

Usage:
    python tools/bench_capture.py <out_path> [duration_s=300]
"""

import serial, time, sys
from pathlib import Path

out = Path(sys.argv[1] if len(sys.argv) > 1 else r'D:\Dripito\github\data\raw\2026-05-14_pm\capture.uart.log')
duration = int(sys.argv[2]) if len(sys.argv) > 2 else 300

out.parent.mkdir(parents=True, exist_ok=True)
print(f'Opening COM3 at 115200, writing to {out}', flush=True)

s = serial.Serial(port='COM3', baudrate=115200, timeout=0.3,
                  xonxoff=False, rtscts=False, dsrdtr=False)

total = 0
drop_count = 0
raw_block_count = 0
reject_count = 0
t0 = time.time()
last_log = t0

with open(out, 'wb') as f:
    while time.time() - t0 < duration:
        chunk = s.read(8192)
        if chunk:
            f.write(chunk); f.flush()
            total += len(chunk)
            text = chunk.decode('utf-8', errors='replace')
            drop_count += text.count('\nDROP,')
            raw_block_count += text.count('DROP_RAW_BEGIN')
            reject_count += text.count('DROP_REJECT')
        if time.time() - last_log > 5:
            print(f'[t+{time.time()-t0:.0f}s] total={total}B drops={drop_count} raw_blocks={raw_block_count} rejects={reject_count}', flush=True)
            last_log = time.time()

s.close()
print(f'DONE. total={total}B drops={drop_count} raw_blocks={raw_block_count} rejects={reject_count}', flush=True)
