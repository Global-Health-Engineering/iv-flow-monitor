"""Apply 2026-04-02 DigiKey invoice corrections to bom.csv.new.

DigiKey order INTERNET 02-APR-2026 / A0FX, paid by Leandro Catarci.
All prices in CHF; converted to USD at FX 0.90 (1 CHF = $1.11).
"""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
src = Path('C:/Users/lcatarci/AppData/Local/Temp/bom_final.csv')
rows = list(csv.reader(src.open(encoding='utf-8')))
header, *data = rows
data = [r for r in data if r and len(r) >= len(header)]
idx = {h: i for i, h in enumerate(header)}


def fx(chf: float) -> float:
    """CHF -> USD at FX 0.90."""
    return chf / 0.90


# Updates to existing rows (find by lcsc_pn or signature) ---------------------
for row in data:
    lcsc = row[idx['lcsc_pn']]
    ref = row[idx['ref']]

    if lcsc == 'C118288':  # D1+D2 BPV10NF
        row[idx['manufacturer']] = 'Vishay'
        row[idx['mfg_pn']] = 'BPV10NF'
        row[idx['digikey_pn']] = '751-1002-ND'
        row[idx['price_usd_1']] = f'{fx(0.578):.4f}'  # = 0.6422
        row[idx['price_usd_1k']] = '0.32'  # estimate 50% LCSC tier
        row[idx['notes']] = 'DigiKey CHF 0.578 each (2026-04-02 invoice) | qty=1000 estimate ~50% LCSC tier'

    elif 'VSMY2940RG' in row[idx['description']] or lcsc == 'C5452771':
        # LED1+LED2 — SKU change from VSMY2940RG to VSLY5940
        row[idx['lcsc_pn']] = ''
        row[idx['digikey_pn']] = 'VSLY5940-ND'
        row[idx['description']] = 'VSLY5940 940 nm IR LED (TOP + BOT emitters)'
        row[idx['mfg_pn']] = 'VSLY5940'
        row[idx['manufacturer']] = 'Vishay'
        row[idx['datasheet']] = ''
        row[idx['price_usd_1']] = f'{fx(0.814):.4f}'  # = 0.9044
        row[idx['price_usd_1k']] = '0.45'  # estimate
        row[idx['notes']] = 'DigiKey CHF 0.814 each (2026-04-02 invoice); SKU revised from VSMY2940RG (LCSC) to VSLY5940 (DigiKey actual)'

    elif ref == '—' and 'FFC ribbon' in row[idx['description']]:
        # FFC cable — GCT EMEA from DigiKey, not Alibaba
        row[idx['manufacturer']] = 'GCT EMEA'
        row[idx['mfg_pn']] = '05-06-A-0101-A-4-06-4-T'
        row[idx['digikey_pn']] = '2073-05-06-A-0101-A-4-06-4-T-ND'
        row[idx['description']] = 'GCT 6-pin 0.5 mm FFC, 3.98 in (~10 cm)'
        row[idx['price_usd_1']] = f'{fx(0.81):.4f}'  # = 0.9000
        row[idx['price_usd_1k']] = '0.40'  # DigiKey vol break estimate
        row[idx['notes']] = 'DigiKey CHF 0.81 each (2026-04-02 invoice) | qty=1000 estimate ~half DigiKey list'


# New rows: U3 LCD + S1+S2+S3 switches (not on JLCPCB invoice) ----------------
new_rows = [
    ['pcb', 'U3', 'Display', 'EA DOGS164W-A 4x16 transflective LCD', 'Display Visions',
     'EA DOGS164W-A', '', '1481-1306-ND', 'EA_DOGS164X-A', '1',
     f'{fx(6.45):.4f}', '4.30', '', 'DigiKey CHF 6.45 each (2026-04-02 invoice) | qty=1000 estimate ~40% discount'],
    ['pcb', 'S1+S2+S3', 'Switch', 'PTS647SN38 tactile switch (Reset/Mode/Mute)', 'C&K',
     'PTS647SN38SMTR2 LFS', '', '108-PTS647SN38SMTR2LFSCT-ND', 'SW_SPST_PTS647_Sx38', '3',
     f'{fx(0.182):.4f}', '0.13', '', 'DigiKey CHF 0.182 each (2026-04-02 invoice); excluded from PCBA, hand-soldered | qty=1000 estimate ~30-50% DigiKey volume'],
]

# Insert U3 right after U1 (boost), and PTS647 in the connector cluster.
final_data = []
inserted_u3 = False
inserted_sw = False
for row in data:
    final_data.append(row)
    if row[idx['ref']] == 'U1' and not inserted_u3:
        final_data.append(new_rows[0])
        inserted_u3 = True
    if row[idx['ref']] == 'SW1' and not inserted_sw:
        final_data.append(new_rows[1])
        inserted_sw = True

with src.open('w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(header)
    w.writerows(final_data)


def to_f(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


g_qty1 = g_qty1k = 0.0
complete_1k = True
for row in final_data:
    qpb = int(row[idx['qty_per_unit']]) if row[idx['qty_per_unit']] else 1
    p1 = to_f(row[idx['price_usd_1']])
    p1k = to_f(row[idx['price_usd_1k']])
    if p1 is not None:
        g_qty1 += p1 * qpb
    if p1k is not None:
        g_qty1k += p1k * qpb
    else:
        complete_1k = False

print(f'rows: {len(final_data)} (was 37)')
print(f'qty=1   grand total: ${g_qty1:.2f}')
print(f'qty=1k  grand total: ${g_qty1k:.2f} {"(COMPLETE)" if complete_1k else "(incomplete)"}')
