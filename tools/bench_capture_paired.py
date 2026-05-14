"""Parallel scale + UART capture for the 2026-05-14 PM session.

Tares the Mettler scale, then streams scale grams + Dripito UART
simultaneously to position-tagged files. Both loggers run for the same
duration in independent threads.

Usage:
    python tools/bench_capture_paired.py <position_tag> [duration_s=180]

Writes:
    data/raw/2026-05-14_pm/<tag>.uart.log
    data/raw/2026-05-14_pm/<tag>_scale.csv
"""

from __future__ import annotations

import csv
import serial
import sys
import threading
import time
from pathlib import Path

UART_PORT = 'COM3'
UART_BAUD = 115200
SCALE_PORT = 'COM4'
SCALE_BAUD = 9600

REPO_ROOT = Path(__file__).resolve().parents[1]


def tare_scale():
    """Tare the Mettler balance. Blocks until response."""
    s = serial.Serial(SCALE_PORT, SCALE_BAUD, timeout=3.0)
    s.reset_input_buffer()
    s.write(b'T\r\n'); s.flush()
    time.sleep(0.5)
    resp = s.read(64)
    s.close()
    print(f'  tare response: {resp!r}')
    return resp


def capture_uart(out_path: Path, duration: float, stats: dict):
    s = serial.Serial(UART_PORT, UART_BAUD, timeout=0.3,
                      xonxoff=False, rtscts=False, dsrdtr=False)
    t0 = time.time()
    last_log = t0
    total = 0
    with open(out_path, 'wb') as f:
        while time.time() - t0 < duration:
            chunk = s.read(8192)
            if chunk:
                f.write(chunk); f.flush()
                total += len(chunk)
                text = chunk.decode('utf-8', errors='replace')
                stats['drops'] += text.count('\nDROP,')
                stats['raws'] += text.count('DROP_RAW_BEGIN')
                stats['rejects'] += text.count('DROP_REJECT')
            if time.time() - last_log > 5:
                print(f"  [t+{time.time()-t0:.0f}s] uart: {total}B drops={stats['drops']} raws={stats['raws']} rej={stats['rejects']}", flush=True)
                last_log = time.time()
    s.close()
    stats['uart_bytes'] = total


def capture_scale(out_path: Path, duration: float, stats: dict):
    s = serial.Serial(SCALE_PORT, SCALE_BAUD, timeout=0.5)
    t0 = time.time()
    samples = 0
    with open(out_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['t_s', 'status', 'grams'])
        while time.time() - t0 < duration:
            s.reset_input_buffer()
            s.write(b'SI\r\n'); s.flush()
            t_send = time.time() - t0
            buf = b''
            t_wait = time.time()
            while time.time() - t_wait < 0.3:
                chunk = s.read(64)
                if chunk: buf += chunk
                if b'\r\n' in buf: break
            line = buf.decode('ascii', errors='replace').strip()
            # Example: "S S     43.6324 g"  (status, status_letter, value, unit)
            parts = line.split()
            if len(parts) >= 4 and parts[0] == 'S':
                status = parts[1]
                try:
                    grams = float(parts[2])
                    w.writerow([f'{t_send:.3f}', status, grams])
                    samples += 1
                except ValueError:
                    pass
            time.sleep(0.05)
    s.close()
    stats['scale_samples'] = samples


def main():
    if len(sys.argv) < 2:
        sys.exit('usage: bench_capture_paired.py <position_tag> [duration_s=180]')
    tag = sys.argv[1]
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 180.0

    out_dir = REPO_ROOT / 'data' / 'raw' / '2026-05-14_pm'
    out_dir.mkdir(parents=True, exist_ok=True)
    uart_path = out_dir / f'{tag}.uart.log'
    scale_path = out_dir / f'{tag}_scale.csv'

    print(f'Taring scale on {SCALE_PORT}...')
    tare_scale()
    time.sleep(1)

    print(f'Starting paired capture for {duration:.0f}s')
    print(f'  UART -> {uart_path}')
    print(f'  Scale -> {scale_path}')

    stats = {'drops': 0, 'raws': 0, 'rejects': 0, 'uart_bytes': 0, 'scale_samples': 0}
    t_uart = threading.Thread(target=capture_uart, args=(uart_path, duration, stats))
    t_scale = threading.Thread(target=capture_scale, args=(scale_path, duration, stats))
    t_uart.start()
    t_scale.start()
    t_uart.join()
    t_scale.join()

    print(f'\nDONE.')
    print(f"  UART bytes: {stats['uart_bytes']}, drops: {stats['drops']}, raws: {stats['raws']}, rej: {stats['rejects']}")
    print(f"  Scale samples: {stats['scale_samples']}")


if __name__ == '__main__':
    main()
