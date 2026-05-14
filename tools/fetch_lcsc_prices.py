"""Fetch qty=1 LCSC prices from jlcsearch and emit hardware/bom.csv."""
import urllib.request
import json
import time
import pathlib
import csv

PARTS = [
    # (Cnum, group, ref, category, description, qty_per_unit, mfg, footprint, notes)
    ('C529341','pcb','U2','IC','STM32G071C8T6 Cortex-M0+ MCU',1,'STMicroelectronics','LQFP-48_7x7mm_P0.5mm','Migrated from G030/G031 (lack COMP1+DAC)'),
    ('C73820', 'pcb','U1','IC','TPS610981DSET 1.5-to-3.3V boost',1,'Texas Instruments','DSE0006A','Single-cell Li-ion AA boost'),
    ('C620155','pcb','Y1','Crystal','32.768 kHz LSE crystal',1,'YXC','Crystal_SMD_3215-2Pin_3.2x1.5mm','RTC reference'),
    ('C347476','pcb','Q3','Transistor','AO3401A P-channel MOSFET',1,'Alpha & Omega','SOT-23',''),
    ('C360603','pcb','BZ1','Audio','SFN-1407PA7.6 piezo buzzer',1,'Sonitron','Buzzer_S&S_SFN-1407PA7.6','Driven by Q4 with R17 pull-up'),
    ('C86090', 'pcb','L1','Inductor','LQM21PN4R7MGRD 4.7 uH boost inductor',1,'Murata','L_0805_2012Metric',''),
    ('C77041', 'pcb','C1','Capacitor','10 uF GRM188R60J106ME47D',1,'Murata','C_0603_1608Metric','Boost output'),
    ('C5199900','pcb','TP1+TP2','Test point','Keystone 5000 miniature test point',2,'Keystone','TestPoint_Keystone_5000-5004_Miniature',''),
    ('C2856796','pcb','J4','Connector','FPC-05F-6PH20 6-pin 0.5 mm FFC socket',1,'Jushuo','Jushuo_AFC07-S06FCA-00_1x6-1MP_P0.50_Horizontal','Battery + IR LED satellite'),
    ('C431548','pcb','SW1','Switch','SK12D07VG5 SPDT slide switch',1,'C&K','X_SW_Slide_SPDT_SSK12D07VG5',''),
    ('C2897370','pcb','J1','Connector','PM254-1-07-Z-8.5 7-pin header',1,'XKB','PinHeader_1x07_P2.54mm_Vertical','SWD + USART1'),
    ('C85864', 'pcb','C3','Capacitor','100 nF GCM188R71H104KA57D (HF)',1,'Murata','C_0603_1608Metric',''),
    ('C1591',  'pcb','C5+C9+C10+C12+C14','Capacitor','0.1 uF CL10B104KB8NNNC decoupling',5,'Samsung','C_0603_1608Metric',''),
    ('C1590',  'pcb','C2','Capacitor','100 nF CL10B104KA8NNNC',1,'Samsung','C_0603_1608Metric',''),
    ('C49661', 'pcb','J2+J3','Connector','2.54 mm 1x2 photodiode socket',2,'BOOMELE','PinSocket_1x02_P2.54mm_Vertical',''),
    ('C137632','pcb','R5','Resistor','390 Ohm RC0603JR-07390RL',1,'Yageo','R_0603_1608Metric',''),
    ('C14858', 'pcb','C8+C13','Capacitor','100 pF CL10C101JB8NNNC',2,'Samsung','C_0603_1608Metric','Photodiode AC-couple'),
    ('C22978', 'pcb','R13+R15','Resistor','3.3 kOhm 0603WAF3301T5E',2,'Uniroyal','R_0603_1608Metric','Photodiode pull-up'),
    ('C19666', 'pcb','C15','Capacitor','4.7 uF CL10A475KO8NNNC',1,'Samsung','C_0603_1608Metric',''),
    ('C8545',  'pcb','Q1+Q2+Q4','Transistor','2N7002 N-MOSFET',3,'onsemi','SOT-23','IR LED drivers + buzzer'),
    ('C1648',  'pcb','C6+C7','Capacitor','20 pF CL10C200JB8NNNC LSE load',2,'Samsung','C_0603_1608Metric',''),
    ('C22775', 'pcb','R1+R3+R4+R7+R14+R16+R18','Resistor','100 Ohm 0603WAF1000T5E',7,'Uniroyal','R_0603_1608Metric','Gate series + current limit'),
    ('C4177',  'pcb','R17','Resistor','1.8 kOhm 0603WAF1801T5E',1,'Uniroyal','R_0603_1608Metric','Buzzer pull-up'),
    ('C59461', 'pcb','C4','Capacitor','22 uF CL10A226MQ8NRNC bulk',1,'Samsung','C_0603_1608Metric',''),
    ('C15849', 'pcb','C11+C16','Capacitor','1 uF CL10A105KB8NNNC',2,'Samsung','C_0603_1608Metric',''),
    ('C25804', 'pcb','R11+R12+R19','Resistor','10 kOhm 0603WAF1002T5E',3,'Uniroyal','R_0603_1608Metric','SWD pulls + buzzer gate pull-down'),
    ('C25803', 'pcb','R2+R6+R8+R10','Resistor','100 kOhm 0603WAF1003T5E',4,'Uniroyal','R_0603_1608Metric','Gate pull-down + battery divider'),
]

SAT_MECH = [
    ('satellite','D1+D2','Photodiode','BPV10NF IR photodiode (TOP+BOT)','Vishay','BPV10NF','','751-1054-ND','',2,'','','https://www.vishay.com/docs/81502/bpv10nf.pdf','satellite board; price pending receipt'),
    ('satellite','LED1+LED2','LED','VSMY2940RG 940 nm IR LED (TOP+BOT)','Vishay','VSMY2940RG','','751-1325-ND','',2,'','','https://www.vishay.com/docs/81204/vsmy2940rg.pdf','satellite board; price pending receipt'),
    ('satellite','—','Fabrication','Satellite breakout PCB','JLCPCB','','','','',1,'1.18','1.18','','1.06 CHF at qty=1 and qty=1000 (USD at FX 0.90)'),
    ('mechanical','—','Cable','6-pin 0.5 mm FFC ribbon','—','','','','',1,'','','','main to satellite; price pending receipt'),
    ('mechanical','—','Battery','1x AA Li-ion (1.5 V flat)','Paleblue','Paleblue AA','','','',1,'','','','price pending receipt'),
    ('mechanical','—','Battery holder','Single AA holder','Keystone','2462','','','',1,'','','','price pending receipt'),
    ('mechanical','—','Heat-set','M2 brass heat-set inserts','—','','','','',4,'','','','price pending receipt'),
    ('mechanical','—','Screw','M2 socket-cap screw','—','','','','',4,'','','','price pending receipt'),
    ('mechanical','—','Filament','ASA white FDM (~25 g/device)','—','','','','',1,'','','','price pending receipt'),
    ('mechanical','—','Filament','ASA black FDM (~5 g/device)','—','','','','',1,'','','','price pending receipt'),
]


def fetch_price(cnum: str) -> tuple[float | None, str]:
    url = f'https://jlcsearch.tscircuit.com/api/search?q={cnum}&limit=3'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = json.loads(urllib.request.urlopen(req, timeout=15).read())
    match = None
    for comp in data.get('components', []):
        if str(comp.get('lcsc')) == cnum[1:]:
            match = comp
            break
    if not match and data.get('components'):
        match = data['components'][0]
    if not match:
        return None, ''
    return match.get('price'), match.get('mfr', '')


def main() -> None:
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    rows: list[list] = []
    for (cnum, group, ref, cat, desc, qpb, mfg, fp, notes) in PARTS:
        try:
            price, mpn = fetch_price(cnum)
            mpn_ascii = mpn.encode('ascii', 'replace').decode('ascii')
            print(f'{cnum:<10} {price!s:>10}  {mpn_ascii}')
        except Exception as exc:
            price, mpn = None, ''
            notes = f'{notes} | lookup-failed: {exc}'.strip(' |')
        rows.append([
            group, ref, cat, desc, mfg, mpn, cnum, '', fp, qpb,
            f'{price:.4f}' if price is not None else '', '', '', notes,
        ])
        time.sleep(0.4)

    # PCB fab from JLCPCB order Y9-9959576A
    rows.append([
        'pcb', '—', 'Fabrication',
        'JLCPCB 50x45 mm 2-layer (qty=5 order $3.10 / 5)',
        'JLCPCB', '', '', '', '', 1, '0.62', '', '',
        'Y9-9959576A 2026-04-23',
    ])

    for row in SAT_MECH:
        rows.append(list(row))

    import io, sys
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow([
        'group','ref','category','description','manufacturer','mfg_pn','lcsc_pn',
        'digikey_pn','footprint','qty_per_unit','price_usd_1','price_usd_1k',
        'datasheet','notes',
    ])
    w.writerows(rows)
    sys.stdout.reconfigure(encoding='utf-8')
    print('===CSV-START===')
    print(buf.getvalue())
    print('===CSV-END===')


if __name__ == '__main__':
    main()
