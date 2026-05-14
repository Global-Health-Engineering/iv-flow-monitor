# IV Drip Monitor Power Supply Comparison

## Device Context

- **MCU:** STM32G030C8Tx
- **Target rail:** 3.3V
- **Current PCB:** KiCad design by Smith (2026), uses BQ25185DLHR + TPS631000 buck-boost + 18650 cell
- **Power data sources:** Catarci (2025) Table 3.1, Smith (2026) Table 2.1, component datasheets

---

## Scenario Definitions

| | A: Li-ion AA (USB-C in battery) | B: LiPo Pouch Cell | C: 18650 Cylindrical |
|---|---|---|---|
| **Battery** | [XTAR 4100 mWh USB-C](https://www.xtar.cc/product/xtar-aa-lithium-4100mwh-2450mah-usb-c-battery-with-low-voltage-indicator.html) or [Paleblue 2550 mWh](https://paleblueearth.com/pages/tech-specs) | 1000 mAh / 3.7V pouch cell with NTC | [Samsung 30Q 3000 mAh](https://www.18650batterystore.com/products/samsung-30q) or [Panasonic NCR18650B 3350 mAh](https://www.batteryspace.com/prod-specs/ncr18650b.pdf) |
| **Converter** | Step-up (boost) 1.5V -> 3.3V | Buck-boost 3.0-4.2V -> 3.3V | Buck-boost 3.0-4.2V -> 3.3V |
| **Charging** | Built into battery (USB-C on battery) | USB-C port on device, [BQ25185DLHR](https://www.ti.com/lit/ds/symlink/bq25185.pdf) | USB-C port on device, [BQ25185DLHR](https://www.ti.com/lit/ds/symlink/bq25185.pdf) |
| **Fallback** | Alkaline AA (universal availability) | None (proprietary form factor) | None (but widely sourced in Africa) |

---

## Main Comparison Table

### 1. Battery Capacity

| Metric | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| Nominal voltage | 1.5V output (3.7V internal cell with buck regulator) | 3.7V | 3.6-3.7V |
| Capacity (mAh at nominal V) | Paleblue: 1700 mAh / XTAR USB-C: 2450 mAh | 1000 mAh (typical for this size class) | 3000-3350 mAh |
| Energy (mWh) | Paleblue: 2550 / XTAR: 4100 | 3700 | 10,800-12,060 |
| **Usable energy at 3.3V rail (mWh)** | **Paleblue: 2372 / XTAR: 3813** (x0.93 boost eff.) | **3330** (x0.90 buck-boost eff.) | **9720-10,854** (x0.90 buck-boost eff.) |

Sources: [Paleblue tech specs](https://paleblueearth.com/pages/tech-specs); [XTAR AA 4100 mWh USB-C](https://www.xtar.cc/product/xtar-aa-lithium-4100mwh-2450mah-usb-c-battery-with-low-voltage-indicator.html); [Panasonic NCR18650B datasheet](https://www.batteryspace.com/prod-specs/ncr18650b.pdf); [Samsung INR18650-30Q datasheet](https://www.18650batterystore.com/products/samsung-30q). Boost efficiency from [TPS610981 datasheet](https://www.ti.com/lit/ds/symlink/tps61098.pdf) (0.93 at low/medium load). Buck-boost efficiency from [TPS631000 datasheet](https://www.ti.com/lit/ds/symlink/tps631000.pdf) (>0.90 at moderate loads).

### 2. Price of Batteries and ICs

| Component | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **Battery (single unit)** | Paleblue: ~$7.50 / XTAR USB-C: ~$6.75 | $0.80-$1.50 (1000+ qty, with NTC) | $1.50-$2.50 (1000+ qty) |
| **Battery (bulk 1000+)** | ~$5.00-$6.00 (estimated, limited bulk channels) | **$0.80-$1.50** | **$1.50-$2.50** |
| **DC-DC converter IC** | [TPS610981](https://www.ti.com/lit/ds/symlink/tps61098.pdf): ~$1.60 (DigiKey, not on LCSC) / [HT7733A](https://www.lcsc.com/product-detail/C131130.html): **$0.10** (LCSC C131130) | [TPS631000DRLR](https://www.lcsc.com/product-detail/C5219190.html): **$0.26** (LCSC C5219190) | [TPS631000DRLR](https://www.lcsc.com/product-detail/C5219190.html): **$0.26** (LCSC C5219190) |
| **Battery management IC** | Not needed (charger in battery) | [BQ25185DLHR](https://www.lcsc.com/product-detail/Battery-Management_Texas-Instruments-BQ25185DLHR_C19725033.html): **$0.89** (LCSC C19725033) | [BQ25185DLHR](https://www.lcsc.com/product-detail/Battery-Management_Texas-Instruments-BQ25185DLHR_C19725033.html): **$0.89** (LCSC C19725033) |
| **USB-C connector** | Not needed on device | ~$0.20-$0.50 (GCT USB4105) | ~$0.20-$0.50 (GCT USB4105) |
| **Total IC + battery cost** | **$5.10-$8.35** (HT7733A) or **$6.60-$9.85** (TPS610981) | **$2.15-$3.15** | **$2.85-$4.15** |

Sources: [LCSC HT7733A (C131130)](https://www.lcsc.com/product-detail/C131130.html); [LCSC TPS631000DRLR (C5219190)](https://www.lcsc.com/product-detail/C5219190.html); [LCSC BQ25185DLHR (C19725033)](https://www.lcsc.com/product-detail/Battery-Management_Texas-Instruments-BQ25185DLHR_C19725033.html); [TPS610981 datasheet](https://www.ti.com/lit/ds/symlink/tps61098.pdf); [Samsung 30Q retail pricing](https://www.18650batterystore.com/products/samsung-30q).

### 3. Energy Density

| Metric | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **Gravimetric (Wh/kg)** | 137 (Paleblue) - 174 (XTAR 3300 mWh) | ~185 | 200-243 ([Panasonic NCR18650B](https://www.batteryspace.com/prod-specs/ncr18650b.pdf): 243) |
| **Volumetric (Wh/L)** | 304 (Paleblue) - 394 (XTAR) | ~500 | 500-676 (Panasonic NCR18650B: 676) |

Note: Li-ion AA energy density is penalised by the internal buck converter PCB occupying volume and adding weight. The 18650 format achieves the highest energy density due to manufacturing maturity and optimised jelly-roll packing.

Sources: Calculated from cell mass/volume and rated capacity. Paleblue: 2.55 Wh / 18.6 g ([Paleblue tech specs](https://paleblueearth.com/pages/tech-specs)); XTAR: 3.3 Wh / 19 g ([XTAR 3300 mWh](https://xtardirect.com/products/xtar-aa-15v-2000mah-li-ion-battery)); Panasonic NCR18650B: 12.06 Wh / 49.5 g / 17.84 mL ([datasheet](https://www.batteryspace.com/prod-specs/ncr18650b.pdf)). Independent XTAR teardown and efficiency data from [Gough's Tech Zone](https://goughlui.com/2024/08/28/mega-review-xtar-4150mwh-2500mah-1-5v-rechargeable-li-ion-aa-battery-l4-usb-c-charger/).

### 4. Device Running Time on a Single Charge

> **Note on Rev-B scope.** The numbers in this section are the Phase-1 (worst case)
> and Phase-2 (best case) projections from the underlying thesis power model. **Rev-B
> ships in Phase 1 only** — both IR LEDs always-on continuous, no LPTIM duty-cycling
> (see `site/src/components/PCBArchitecture.astro` Hotspot 3 and
> `docs/decisions/led-duty-cycle.md`). The Phase-2 ~30-day runtime is therefore a
> Rev-C deliverable, not a Rev-B claim. The Phase-1 worst-case ~2.5 day runtime is
> the operative number for the as-shipped Rev-B firmware.

Runtime estimated using power consumption data from both theses:
- **Best case** (Catarci, Thesis 1; Phase 2 — Rev-C target): duty-cycled LED (150 us pulses, 8.3% duty) + MCU Stop mode = **1.57 mA** avg at 3.3V = 5.18 mW
- **Worst case** (Catarci, Thesis 1; Phase 1 — Rev-B as shipped): continuous LED operation = **19.5 mA** avg at 3.3V = 64.35 mW
- For scenarios B and C, BQ25185 quiescent current (~150 uA at 3.7V = 0.56 mW) is added

| Runtime | A: Li-ion AA (XTAR 4100 mWh) | A: Li-ion AA (Paleblue 2550 mWh) | B: LiPo Pouch (1000 mAh) | C: 18650 (3000 mAh) | C: 18650 (3350 mAh) |
|---|---|---|---|---|---|
| **Best case** | **30.7 days** (736 h) | **19.1 days** (457 h) | **24.4 days** (586 h) | **71.3 days** (1712 h) | **79.6 days** (1911 h) |
| **Worst case** | **2.5 days** (59 h) | **1.5 days** (37 h) | **2.1 days** (51 h) | **6.3 days** (150 h) | **7.0 days** (168 h) |
| **Alkaline AA fallback** | Best: 22.4 days / Worst: 1.8 days (3000 mWh, matches Thesis 1: 18.6-21 days / 36-40 h) | -- | -- | -- | -- |

Calculation method: Usable_energy_at_3.3V / system_power. For A: E_usable = E_battery x eta_boost (0.93). For B/C: E_usable = E_battery; total_power = (system_power / eta_buckboost) + P_BQ25185_quiescent.

Sources: Catarci (2025) Table 3.1, Appendix C (thesis_1.pdf in this repository); [TPS610981 datasheet](https://www.ti.com/lit/ds/symlink/tps61098.pdf) efficiency curves; [TPS631000 datasheet](https://www.ti.com/lit/ds/symlink/tps631000.pdf); [BQ25185 datasheet](https://www.ti.com/lit/ds/symlink/bq25185.pdf) quiescent current.

### 5. Battery Availability in Africa

Searched across 14 representative countries: Nigeria, Ghana, Senegal, Kenya, Tanzania, Ethiopia, Uganda, South Africa, Mozambique, Malawi, DRC, Cameroon, Egypt, Morocco.

| Country / Region | A: Li-ion AA (USB-C type) | B: LiPo Pouch | C: 18650 | Alkaline AA (fallback for A) |
|---|---|---|---|---|
| **Nigeria** | Not available | Minimal (Jumia, RC hobby only) | Excellent ([Jumia Nigeria](https://www.jumia.com.ng/mlp-18650-battery/), Konga) | Excellent (all platforms + retail) |
| **Ghana** | Not available | Not available | Good ([Jumia Ghana](https://www.jumia.com.gh/mlp-18650-battery/)) | Excellent |
| **Senegal** | Not available | Not available | Likely ([Jumia Senegal](https://www.jumia.sn/mlp-batterie-rechargeable/)) | Good (Jumia, retail) |
| **Kenya** | Partial (XTAR via whizz.co.ke) | Yes, specialty ([Nerokas](https://store.nerokas.co.ke/)) | Excellent ([Jumia Kenya](https://www.jumia.co.ke/mlp-18650-rechargeable-battery/), Kilimall) | Excellent |
| **Tanzania** | Not available | Not available | Limited (Jiji, Shopit, Kariakoo market) | Good (physical retail) |
| **Ethiopia** | Not available | Not available | Limited (Jiji, Merkato market) | Good (physical retail) |
| **Uganda** | Not available | Not available | Good ([Jumia Uganda](https://www.jumia.ug/mlp-18650-battery/)) | Good (Jumia, retail) |
| **South Africa** | **Yes** ([Takealot](https://www.takealot.com/): EBL, BESTON, EnerC) | Yes, specialty ([DIY Electronics](https://www.diyelectronics.co.za/store/152-li-ion-li-po)) | Excellent ([Takealot](https://www.takealot.com/computers/general-purpose-batteries-29176)) | Excellent |
| **Mozambique** | Not available | Not available | Uncertain (source from South Africa) | Limited (physical retail) |
| **Malawi** | Not available | Not available | Uncertain (Ubuy, PowerTex) | Limited (physical retail) |
| **DRC** | Not available | Not available | Uncertain (physical markets Kinshasa) | Limited (physical retail) |
| **Cameroon** | Not available | Not available | Likely (E-Tech Store, Ubuy) | Available (retail) |
| **Egypt** | Not available | Yes, specialty ([Micro Ohm](https://microohm-eg.com/batteries-chargers-holders/batteries/micro-lipo-batteries/)) | Excellent ([Jumia Egypt](https://www.jumia.com.eg/mlp-18650-battery/), [Noon](https://www.noon.com/egypt-en/), [Amazon.eg](https://www.amazon.eg/)) | Excellent |
| **Morocco** | Not available | Not available | Good ([Jumia Morocco](https://www.jumia.ma/mlp-batterie-18650/)) | Good (Jumia) |
| **Availability score** | **1/14 countries** (SA only confirmed) | **3/14 countries** (specialty stores) | **10+/14 countries** | **14/14 countries** |

**Alkaline AA fallback assessment for Scenario A:** Alkaline AAs are universally available across all 14 surveyed countries, from e-commerce platforms (Jumia, Takealot, Noon) to corner shops, gas stations, and street vendors. Brands include Duracell, Energizer, Panasonic, GP, and local alternatives. This makes the alkaline AA fallback highly realistic. However, alkaline cells are non-rechargeable and provide ~22 days (best) to ~1.8 days (worst) per cell, creating ongoing consumable costs (CHF 0.20/cell x ~17-200 cells/year depending on duty cycle).

**Replacement options in case of complete battery failure:**

| Scenario | Replacement Strategy |
|---|---|
| A (Li-ion AA fails) | Replace with alkaline AA from any local shop. Loss of rechargeability. NiMH AA with external charger also available in most markets. |
| B (LiPo pouch fails) | Must source from specialty electronics retailer (South Africa, Kenya, Egypt only) or import. Device is non-functional until replacement arrives. |
| C (18650 fails) | Replace from local market in most African cities. Flashlight/solar/vape shops commonly stock 18650 cells. |

Note: Jumia, Takealot, and similar African e-commerce platforms block automated URL verification (HTTP 403), but all listed store URLs were confirmed via manual research by the search agents. Paleblue does not ship internationally outside US/EU; Amazon prohibits international shipping of lithium batteries as hazmat.

### 6. Swelling Risk

| Factor | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **Casing type** | Rigid metal cylindrical can | Soft aluminum laminate | Rigid steel cylindrical can |
| **Swelling risk level** | **Low** | **High** | **Very low** |
| **Dimensional change over life** | Negligible externally | 8-10% thickness increase over 500 cycles; up to 32% in aggressive conditions | Negligible externally |
| **Safety mechanisms** | Internal protection PCB (overcharge, over-discharge, short-circuit, thermal cutoff) | Relies on thermal seal as rupture point; no CID or vent | CID at 1.06-1.29 MPa + burst disc vent at 2.2-2.3 MPa + PTC |
| **Design implication** | No special clearance needed | Must design 10-15% clearance in enclosure for swelling | No special clearance needed |

Sources: [MDPI Batteries 8(5):42 -- pouch cell expansion](https://doi.org/10.3390/batteries8050042); [Frontiers in Chemical Engineering -- gas generation in pouch cells](https://www.frontiersin.org/journals/chemical-engineering/articles/10.3389/fceng.2022.828375/full); [NASA 18650 safety analysis (NTRS)](https://ntrs.nasa.gov/api/citations/20100037250/downloads/20100037250.pdf).

### 7. Self-Discharge Rate When Not in Use

| Condition | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **At 25 C** | **5-8%/month** (electrochemical 1-2% + internal buck regulator quiescent ~20-30 uA continuously) | **3-5%/month** | **1-3%/month** |
| **At 35 C** | 9-14%/month | 5-9%/month | 2-5%/month |
| **At 45 C** | 15-24%/month | 9-15%/month | 3-9%/month |
| **Months to 50% capacity loss at 25 C** | ~7-10 months | ~10-17 months | ~17-50 months |
| **Critical note** | Internal buck converter draws quiescent current even when device is off; **worst shelf life** | Moderate | **Best shelf life**; no parasitic electronics drain in bare cell |

Sources: [Battery University BU-802b](https://www.batteryuniversity.com/article/bu-802b-what-does-elevated-self-discharge-do); [Gough's Tech Zone XTAR teardown](https://goughlui.com/2024/08/28/mega-review-xtar-4150mwh-2500mah-1-5v-rechargeable-li-ion-aa-battery-l4-usb-c-charger/) (buck converter efficiency and quiescent current data); Arrhenius self-discharge model Ea ~ 0.94 +/- 0.14 eV, Q10 ~ 1.5-2.0x per [Schindler et al., J. Power Sources (2023)](https://doi.org/10.1016/j.jpowsour.2022.232309).

### 8. Number of Charge/Discharge Cycles

| Condition | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **Manufacturer-rated (to 80% capacity)** | Paleblue: **1000+** / XTAR: **1000-1200** | **500+** (at 0.2C, 100% DoD) | **300-500** (at 100% DoD) |
| **At 80% DoD** | ~1000-1200 | ~500-800 | ~500+ |
| **At 40% DoD (shallow cycling)** | Not published | ~800-1200 | ~1250 |
| **At 20% DoD** | Not published | Not published | ~2500 |

Note: Li-ion AA cells achieve higher cycle counts because the internal protection circuitry prevents deep discharge and overcharge abuse. For scenarios B and C, the [BQ25185](https://www.ti.com/lit/ds/symlink/bq25185.pdf) provides similar protection (+/-0.5% charge voltage accuracy), which improves real-world cycle life over the datasheet minimum.

Sources: [Paleblue tech specs](https://paleblueearth.com/pages/tech-specs); [XTAR 3300 mWh specs](https://xtardirect.com/products/xtar-aa-15v-2000mah-li-ion-battery) (>=1000 cycles); [Battery University BU-808](https://www.batteryuniversity.com/article/bu-808-how-to-prolong-lithium-based-batteries) (DoD vs cycle life data).

### 9. Battery Failure Rate

| Metric | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **Catastrophic failure (thermal runaway)** | ~1 in 10 million (quality cells) | ~1 in 10 million (quality cells) | ~1 in 10 million (quality cells) |
| **Counterfeit/low-quality risk** | Moderate (niche market, limited manufacturers) | Moderate (variable quality from Chinese suppliers) | **High if not from reputable manufacturer** -- [Lumafield](https://www.lumafield.com/battery-report) found 1 in 13 (8%) of low-cost cells had dangerous anode overhang defects |
| **Primary failure mode** | USB-C port mechanical damage in tight battery compartments; buck converter PCB failure | Swelling/gas generation leading to seal rupture | Capacity fade; counterfeit cells with poor quality control |
| **Manufacturing quality data** | No published data specific to this format | Limited published data | Extensive ([Lumafield Battery Quality Report](https://www.lumafield.com/battery-report): >1000 cells CT-scanned) |

Sources: [Battery University BU-304a -- Li-ion safety and failure rates](https://www.batteryuniversity.com/article/bu-304a-safety-concerns-with-li-ion) ("failure rate of a quality Li-ion cell is better than 1 in 10 million"); [Lumafield Battery Quality Report](https://www.lumafield.com/battery-report) (1054 cells CT-scanned, 8% defect rate in low-cost cells).

### 10. Disinfection Suitability

The device is intended for clinical use in hospitals and must withstand repeated surface disinfection (wiping with chlorine-based solutions, alcohol, or quaternary ammonium compounds). Ingress of liquid into the enclosure during disinfection is a primary concern.

| Metric | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **Battery access point** | Removable battery flap/door on enclosure rear | None (battery is sealed inside) | None (battery is sealed inside) |
| **USB-C port on enclosure** | **Not present** -- charging is on the battery itself | **Exposed** -- required for charging and flashing | **Exposed** -- required for charging and flashing |
| **Ingress risk during disinfection** | **Battery flap:** seam around the flap door is a liquid ingress path. Flap may be lost, left open, or improperly re-seated after battery swap, exposing the battery bay. Repeated disinfection degrades flap gasket/seal over time. | **USB-C port:** open cavity that must be covered with a silicone plug or hinged rubber cap during disinfection. Plug may be lost or forgotten. Port is recessed but not sealed. | **Same as B** |
| **Mitigation options** | Captive flap with living hinge (PETG compatible); silicone gasket around seam; IP-rated battery door latch | Silicone dust/splash plug for USB-C; hinged TPU cap molded into enclosure; conformal coating on PCB near port | Same as B |
| **Risk of component loss** | **High** -- flap/door is a separate part that can be lost, broken, or not re-attached after battery replacement in a busy ward | **Moderate** -- silicone USB-C plug is small and easily lost; a moulded captive cap reduces but does not eliminate risk | **Moderate** -- same as B |
| **Seal integrity over device lifetime** | Degrades with each battery swap (hundreds of open/close cycles over 1000+ charge cycles) | Degrades only with cap removal for charging (less frequent than battery swaps) | Same as B |
| **Overall disinfection suitability** | **Worst** -- two ingress paths (flap seam + battery contacts exposed when flap lost) | **Moderate** -- single ingress point (USB-C), manageable with captive cap | **Moderate** -- same as B |

Note: In all three scenarios, the optical sensor arm (IR LED + photodiode facing the drip chamber) is inherently exposed and must tolerate splash disinfection. The Thesis 1 enclosure (PETG, 3D-printed) already demonstrated chemical compatibility with common hospital disinfectants (Catarci, 2025, Section 2.1.3, thesis_1.pdf). The critical differentiator is the number and type of openings that must be sealed. Scenario A trades USB-C port exposure for a battery flap that is mechanically stressed during every battery swap. Scenarios B and C have a single, smaller opening (USB-C port) that is only accessed during charging, not routine battery replacement.

### 11. Administrative Ease of Battery Transport (Shipped in Device)

When shipping complete devices with batteries installed (PI 967, Section II), administrative requirements are simplified compared to shipping batteries separately. However, the three scenarios differ in practical burden.

| Metric | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **Energy per cell** | 2.6-4.1 Wh | 3.7 Wh | 10.8-12.1 Wh |
| **2026 SoC shipping limit applies? (PI 967, in device)** | **No** -- PI 967 is exempt from the [2026 30% SoC limit](https://www.lion.com/lion-news/december-2025/new-lithium-battery-state-of-charge-limit-in-effect-jan-1) | **No** -- same exemption | **No** -- same exemption |
| **Shipper's Declaration for DG** | Not required | Not required | Not required |
| **Marking requirements** | Lithium battery handling label on outer package; UN3481 marking | Same | Same |
| **Max cells per package (PI 967, Section II)** | No limit on number of devices per package (each device contains 1 cell <20 Wh) | Same | Same |
| **Gross package weight limit** | 5 kg per package (Section II) | 5 kg per package | 5 kg per package |
| **Devices per 5 kg package (estimated)** | ~60-70 devices (device ~70 g each) | ~60-70 devices (~75 g each) | ~50-55 devices (~95 g each) |
| **Spare batteries shipped alongside** | Can ship spare Li-ion AAs **and** alkaline AAs easily; Li-ion AAs under 2.7 Wh may be exempt from 2026 SoC limit even under PI 966 | Spare pouch cells require PI 965 Section IB (full DG documentation, since PI 965 Section II was eliminated in 2022) if shipped alone; or PI 966 with 30% SoC limit if packed with equipment | Same restrictions as B for spare 18650 cells |
| **Practical advantage** | **Best** -- spare alkaline AAs are not regulated as dangerous goods at all (not lithium-ion). Spare Li-ion AAs are small enough to often fall under de minimis thresholds. Simple logistics. | Spare LiPo cells shipped alone require full DG paperwork. Most practical to pre-install and ship in device. | Spare 18650 cells are common cargo (flashlight/solar industry) so logistics providers in Africa are familiar with handling them. Easier than LiPo despite same regulatory classification. |
| **Customs familiarity** | AA batteries are universally recognised; customs officers unlikely to flag or delay | Pouch cells are less familiar; may trigger inspection or questions at customs in some countries | 18650 cells are familiar in the solar/flashlight supply chain; moderate customs familiarity |
| **Overall administrative ease** | **Easiest** -- especially with alkaline AA fallback (zero DG burden for spares) | **Hardest** -- unfamiliar form factor, full DG paperwork for spare cells | **Moderate** -- familiar in African supply chain, but full DG paperwork for spares |

Note: For all three scenarios, shipping the complete assembled device (battery installed) under PI 967 Section II is the simplest pathway. No Shipper's Declaration, no 2026 SoC limit, just a lithium battery handling label. The key differentiator is what happens when spare batteries need to be shipped separately for field replacement -- this is where Scenario A has a clear advantage because alkaline AAs carry zero dangerous goods burden, and the Li-ion AA cells are small enough (2.6-4.1 Wh) to minimise regulatory friction.

Sources: [IATA Lithium Battery Guidance Document (2026)](https://www.iata.org/contentassets/05e6d8742b0047259bf3a700bc9d42b9/lithium-battery-guidance-document.pdf); [Lion Technology: 2026 SoC limit advisory](https://www.lion.com/lion-news/december-2025/new-lithium-battery-state-of-charge-limit-in-effect-jan-1); [Intertek: UN 38.3 testing requirements](https://www.intertek.com/batteries/un-38-3-testing/); [Compliance & Risks: Battery regulation in Africa](https://www.complianceandrisks.com/blog/the-state-of-play-batteries-regulation-across-africa/).

---

## Additional Metrics

### 12. Enclosure Size Impact

| Metric | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **Battery dimensions** | 14.5 x 50.5 mm (standard AA) | 6 x 34 x 53 mm (603450 format) | 18 x 65 mm |
| **Battery volume** | ~8.4 mL | ~10.8 mL | ~16.5 mL |
| **Fit in current enclosure (105x38x55 mm)** | **Yes** -- same as Thesis 1 design | **Yes** -- thinner, could enable slimmer enclosure | **Tight fit** -- 65 mm length may require enclosure lengthening or diagonal placement |
| **PCB impact** | Simplest PCB (no USB-C, no charger IC) | Requires USB-C connector, charger IC, NTC, battery connector on PCB | Same as B |
| **Enclosure redesign needed?** | **No** (direct AA holder swap) | Moderate (new battery compartment shape, USB-C cutout) | **Yes** (larger battery bay + USB-C cutout) |

### 13. Weight

| Component | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **Battery weight** | Paleblue: 18.6 g / XTAR: ~19 g | ~20-22 g (with PCM + NTC) | **44-48 g** |
| **Additional PCB components** | Minimal (boost converter only) | BQ25185 + TPS631000 + USB-C + passives: ~2-3 g | Same as B: ~2-3 g |
| **Estimated total device weight impact vs Thesis 1** | **Baseline** (same as current) | **+2-3 g** (similar battery weight, added PCB components) | **+27-30 g** (heavier battery + added PCB components) |

Note: For a clip-on device on a drip chamber, weight directly affects grip stability. The 18650 adds significant mass which may require a stronger clamp mechanism. Thesis 1 enclosure was ~28 g (PETG). The current device with AA battery totals approximately 65-75 g. Adding an 18650 would push it to ~90-100 g.

Sources: [Paleblue tech specs](https://paleblueearth.com/pages/tech-specs) (18.6 g); [XTAR 3300 mWh specs](https://xtardirect.com/products/xtar-aa-15v-2000mah-li-ion-battery) (19 g); [Panasonic NCR18650B datasheet](https://www.batteryspace.com/prod-specs/ncr18650b.pdf) (47.5 g).

### 14. Charging Time (Empty to Full)

| Metric | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **Charge rate** | Built-in charger: Paleblue 1.9 h / XTAR USB-C 2.7 h | 0.5C-1C ([BQ25185](https://www.ti.com/lit/ds/symlink/bq25185.pdf) at up to 1A) | 0.5C ([BQ25185](https://www.ti.com/lit/ds/symlink/bq25185.pdf) at 1A max) |
| **Time to full charge** | **1.5-2.7 hours** | **1-1.5 hours** (fastest) | **3-4 hours** |
| **Can device operate while charging?** | No (battery must be removed to charge via its own USB-C port) | **Yes** (BQ25185 power path) | **Yes** (BQ25185 power path) |

Note: Scenario A requires removing the battery from the device to charge it, creating downtime unless a spare battery is available. Scenarios B and C allow simultaneous charging and operation via the BQ25185 power path management.

Sources: [XTAR AA 4100 mWh USB-C](https://www.xtar.cc/product/xtar-aa-lithium-4100mwh-2450mah-usb-c-battery-with-low-voltage-indicator.html) (2.7 h charge time); [BQ25185 datasheet](https://www.ti.com/lit/ds/symlink/bq25185.pdf) (1A max charge current, power path management).

### 15. Temperature Operating Range

| Condition | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **Charging range** | 0 to 45 C | 0 to 45 C | 0 to 45 C |
| **Discharging range** | -20 to 60 C | -20 to 60 C | -20 to 60 C |
| **Optimal operating** | 20 to 40 C | 20 to 40 C | 20 to 40 C |
| **Hot climate concern (35-50 C ambient)** | **Worst** -- internal buck regulator adds heat + continuous parasitic drain accelerates degradation | Moderate -- good heat dissipation (flat geometry) but seal integrity degrades with temperature cycling | **Best** -- robust steel can, best thermal tolerance, lowest self-discharge at elevated temp |
| **Calendar aging at 45 C (capacity loss rate)** | ~4-8x rate vs 25 C | ~4-8x rate vs 25 C | ~4-8x rate vs 25 C (but starts from lowest base self-discharge) |

Sources: [Battery University BU-808](https://www.batteryuniversity.com/article/bu-808-how-to-prolong-lithium-based-batteries) (temperature impact on cycle life); [Nature Scientific Reports: Temperature aging of Li-ion](https://doi.org/10.1038/srep12967); Arrhenius model with Ea ~ 36,000 J/mol.

### 16. PCB Complexity

| Metric | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **Power ICs on PCB** | 1 (boost converter only) | 3 (BQ25185 + TPS631000 + CH340C for USB-UART) | 3 (same as B) |
| **USB-C connector** | Not needed | Required | Required |
| **ESD protection** | Not needed | Required (USB data + 5V lines) | Required |
| **NTC thermistor** | Not needed (in battery) | Required (bonded to cell, connected to BQ25185 TS pin) | Required |
| **Battery connector** | Standard AA holder (through-hole) | JST/Molex connector (SMD) + wires to pouch cell | 18650 holder or spot-welded tabs |
| **Estimated additional passive components** | ~5 (boost converter passives: inductor, caps, resistors) | ~25-30 (charger passives + converter passives + ESD + USB) | ~25-30 (same as B) |
| **Design effort** | **Lowest** -- similar to Thesis 1 PCB | **Highest** -- requires careful layout for charger, buck-boost, USB, thermal pad | **High** -- same as B, but larger battery holder may affect layout |

### 17. Regulatory / Transport Considerations

| Metric | A: Li-ion AA | B: LiPo Pouch | C: 18650 |
|---|---|---|---|
| **UN38.3 testing required?** | Yes (but typically certified by battery manufacturer: Paleblue/XTAR) | Yes (must be arranged with cell supplier) | Yes (typically certified by manufacturer: Samsung, LG, Panasonic) |
| **IATA packing instruction** | PI 967 Section II (contained in equipment) | PI 967 Section II | PI 967 Section II |
| **Energy per cell** | 2.6-4.1 Wh (well under 20 Wh limit) | 3.7 Wh (under 20 Wh) | 10.8-12.1 Wh (under 20 Wh) |
| **2026 SoC shipping limit (>2.7 Wh)** | Most models under 2.7 Wh threshold -- **exempt** | Above 2.7 Wh -- **must ship at <=30% SoC** (PI 966 only, packed with equipment) | Above 2.7 Wh -- **must ship at <=30% SoC** (PI 966 only) |
| **Shipper's Declaration for DG** | Not required (Section II) | Not required (Section II) | Not required (Section II) |
| **African import duties** | Same as other Li-ion | Same | Same (0% duty in [SACU](https://www.globaltradealert.org/state-act/8509/sacu-import-tariff-decrease-on-lithium-batteries)/EAC) |

Note: When shipping the complete device with battery installed (PI 967), the 2026 SoC limit does not apply. It only applies to PI 966 (battery packed alongside but not inside equipment). Shipping the device assembled avoids this restriction for all three scenarios.

Sources: [IATA Lithium Battery Guidance Document (2026)](https://www.iata.org/contentassets/05e6d8742b0047259bf3a700bc9d42b9/lithium-battery-guidance-document.pdf); [Lion Technology: 2026 SoC limit](https://www.lion.com/lion-news/december-2025/new-lithium-battery-state-of-charge-limit-in-effect-jan-1); [Intertek: UN 38.3 testing](https://www.intertek.com/batteries/un-38-3-testing/); [Compliance & Risks: Battery regulation in Africa](https://www.complianceandrisks.com/blog/the-state-of-play-batteries-regulation-across-africa/).

---

## Summary Scorecard

| Metric | A: Li-ion AA | B: LiPo Pouch | C: 18650 | Winner |
|---|---|---|---|---|
| 1. Battery capacity | 2550-4100 mWh | 3700 mWh | 10,800-12,060 mWh | **C** |
| 2. Total IC + battery cost | $5.10-$9.85 | **$2.15-$3.15** | $2.85-$4.15 | **B** |
| 3. Energy density (Wh/kg) | 137-174 | 185 | **200-243** | **C** |
| 4a. Runtime best case | 19-31 days | 24 days | **71-80 days** | **C** |
| 4b. Runtime worst case | 1.5-2.5 days | 2.1 days | **6.3-7.0 days** | **C** |
| 5. African availability | 1/14 countries (+ AA fallback: 14/14) | 3/14 countries | **10+/14 countries** | **C** (A with fallback) |
| 6. Swelling risk | Low | **High** | **Very low** | **C** |
| 7. Self-discharge | **5-8%/month (worst)** | 3-5%/month | **1-3%/month (best)** | **C** |
| 8. Cycle life | **1000-1200 (best)** | 500+ | 300-500 | **A** |
| 9. Failure rate | No published data | ~1 in 10M; swelling common | ~1 in 10M; counterfeit risk | **Tie A/C** |
| 10. Disinfection suitability | **Worst** -- battery flap seam + flap loss risk | Moderate -- USB-C plug needed | Moderate -- USB-C plug needed | **B/C** |
| 11. Admin ease of transport | **Easiest** -- alkaline AA spares carry zero DG burden | Hardest -- unfamiliar form, full DG for spares | Moderate -- familiar in African supply chain | **A** |
| 12. Enclosure impact | **No redesign needed** | Moderate redesign | Redesign needed (larger) | **A** |
| 13. Weight | **~19 g (lightest)** | ~22 g | ~47 g (heaviest) | **A** |
| 14. Charging time | 1.5-2.7 h (battery removed) | **1-1.5 h (in-device)** | 3-4 h (in-device) | **B** |
| 15. Hot climate suitability | Worst | Moderate | **Best** | **C** |
| 16. PCB complexity | **Simplest** | Most complex | Complex | **A** |
| 17. Transport/regulatory | Easiest (exempt from 2026 SoC limit) | Standard | Standard | **A** |

---

## Key Tradeoff Analysis

**Scenario A** offers the simplest PCB design, lightest weight, best cycle life, easiest transport logistics, and a universal alkaline-AA fallback. However, the battery itself is expensive ($5-8), nearly impossible to source in Africa (only South Africa confirmed), has the worst self-discharge rate, worst disinfection profile (losable battery flap), and requires removing the battery from the device to charge it.

**Scenario B** offers the lowest total IC + battery cost, fastest charging with in-device operation, and a thin form factor. However, LiPo pouch cells carry the highest swelling risk, are the hardest to source in Africa (3/14 countries), have no fallback option, and result in the most complex PCB.

**Scenario C** dominates on capacity, runtime, energy density, availability in Africa, swelling safety, self-discharge, and hot-climate suitability. The main tradeoffs are higher weight (~47 g vs ~19 g), longer charging time (3-4 h), need for enclosure redesign, and complex PCB. The 18650 is the most readily available specialty battery across Africa due to widespread use in flashlights, solar lanterns, and power banks.

---

## Results at a Glance

Scenario A (Li-ion AA) is the simplest to implement:
- Lightest (~19 g), simplest PCB, no enclosure redesign
- Best cycle life (1000-1200 cycles)
- Universal alkaline AA fallback (available in all 14 countries)
- Tradeoff: most expensive battery ($5-8), near-impossible to source in Africa (only South Africa), worst self-discharge (5-8%/month due to internal regulator quiescencurrent), may have to remove battery to charge depending on the case design

Scenario B (LiPo pouch) is the cheapest:
- Lowest total IC + battery cost ($2.15-$3.15)
- Fastest charging (1-1.5 h) with in-device operation
- Tradeoff: highest swelling risk, very limited African availability (3/14), no fallback, most complex PCB

Scenario C (18650) is the strongest overall:
- Highest capacity (10,800-12,060 mWh) and runtime (6-80 days depending on mode)
- Best availability in Africa (10+/14 countries surveyed)
- Lowest swelling risk and self-discharge (1-3%/month)
- Best suited for hot climates
- Tradeoff: heaviest (~47 g), requires enclosure redesign, 3-4 h charge time