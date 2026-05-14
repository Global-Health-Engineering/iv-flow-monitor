"""Fill qty=1000 estimates into hardware/bom.csv.new.

Multipliers:
- LCSC Extended ICs: ~50% of qty=1
- LCSC Extended cheap items: ~70-80% (small absolute savings)
- LCSC Basic parts (already at minimum): same as qty=1
- BPV10NF / VSMY2940RG: 50% (LCSC retail at qty=1000 break)
- JLCPCB fab: $0.30 at qty=1000 typical
- AA holder: $0.50 bulk
- ASA filament: $0.65 white, $0.13 black (slight bulk discount)
- AliExpress items (battery, FFC, satellite, bezel): flat (already populated)

Each row updated here gets ` (est qty=1000)` appended to notes.
"""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Per-piece qty=1000 estimates keyed by LCSC code or row signature
LCSC_ESTIMATES = {
    'C529341': 0.83,   # STM32G071
    'C73820':  0.61,   # TPS610981
    'C620155': 0.12,   # Y1 crystal
    'C347476': 0.023,  # AO3401A
    'C360603': 0.043,  # BZ1
    'C86090':  0.042,  # L1
    'C77041':  0.007,  # C1
    'C5199900': 0.148, # TP1+2
    'C2856796': 0.055, # J4
    'C431548': 0.016,  # SW1
    'C2897370': 0.068, # J1
    'C85864':  0.008,  # C3
    'C1591':   0.002,  # C5+9+10+12+14
    'C1590':   0.002,  # C2
    'C49661':  0.025,  # J2+3
    'C137632': 0.001,  # R5
    'C118288': 0.24,   # BPV10NF
    'C5452771': 0.25,  # VSMY2940RG
}

# For LCSC basics where qty=1000 equals qty=1 (already at minimum)
BASIC_FLAT = {
    'C14858', 'C22978', 'C19666', 'C8545', 'C1648',
    'C22775', 'C4177', 'C59461', 'C15849', 'C25804', 'C25803',
}

src = Path('C:/Users/lcatarci/AppData/Local/Temp/bom_final.csv')
rows = list(csv.reader(src.open(encoding='utf-8')))
header, *data = rows
idx = {h: i for i, h in enumerate(header)}

data = [r for r in data if r and len(r) >= len(header)]
for row in data:
    lcsc = row[idx['lcsc_pn']]
    qty1 = row[idx['price_usd_1']]
    qty1k = row[idx['price_usd_1k']]
    desc = row[idx['description']]
    notes = row[idx['notes']]

    if qty1k:
        continue  # already populated

    if lcsc in LCSC_ESTIMATES:
        row[idx['price_usd_1k']] = f'{LCSC_ESTIMATES[lcsc]:.4f}'
        row[idx['notes']] = (notes + ' | qty=1000 estimate (~50% of LCSC qty=1)').lstrip(' |')
    elif lcsc in BASIC_FLAT:
        row[idx['price_usd_1k']] = qty1
        row[idx['notes']] = (notes + ' | qty=1000 = qty=1 (LCSC Basic; no volume tier)').lstrip(' |')
    elif 'PCB fab' in desc or '50x45 mm 2-layer' in desc:
        row[idx['price_usd_1k']] = '0.30'
        row[idx['notes']] = (notes + ' | qty=1000 estimate ($0.30/board at JLCPCB volume order)').lstrip(' |')
    elif 'Single AA holder' in desc:
        row[idx['price_usd_1k']] = '0.50'
        row[idx['notes']] = (notes + ' | qty=1000 estimate (bulk Keystone)').lstrip(' |')
    elif 'ASA white' in desc:
        row[idx['price_usd_1k']] = '0.65'
        row[idx['notes']] = (notes + ' | qty=1000 estimate (slight bulk filament discount)').lstrip(' |')
    elif 'ASA black' in desc:
        row[idx['price_usd_1k']] = '0.13'
        row[idx['notes']] = (notes + ' | qty=1000 estimate (slight bulk filament discount)').lstrip(' |')

with src.open('w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(header)
    w.writerows(data)

# Print qty=1000 grand total
def to_f(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None

g_qty1 = 0.0
g_qty1k = 0.0
qty1k_complete = True
for row in data:
    qpb = int(row[idx['qty_per_unit']]) if row[idx['qty_per_unit']] else 1
    p1 = to_f(row[idx['price_usd_1']])
    p1k = to_f(row[idx['price_usd_1k']])
    if p1 is not None:
        g_qty1 += p1 * qpb
    if p1k is not None:
        g_qty1k += p1k * qpb
    else:
        qty1k_complete = False

print(f'qty=1   grand total: ${g_qty1:.2f}')
print(f'qty=1k  grand total: ${g_qty1k:.2f} {"(COMPLETE)" if qty1k_complete else "(incomplete)"}')
