# hardware/IV_Flow_Monitor_Footprints.pretty/

Project-local KiCad **footprint** library (the `.pretty/` directory
naming is KiCad's convention for a footprint library). Symbols live
separately in `../lib/`.

## Contents

| File | What it is |
|------|------------|
| `EA_DOGS164X-A.kicad_mod` | DOGS164W-A 4×16 character LCD module |
| `Buzzer_S&S_SFN-1407PA7.6.kicad_mod` | Piezo buzzer |
| `PTS647SN38SMTR2_LFS.kicad_mod` (in `../lib/`-pair) | Tactile switch — see `../lib/` for matching symbol |
| `SW_HYP_1TS005F-2500-5001.kicad_mod` | Slide-switch alternate footprint |
| `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.kicad_mod` | USB-C receptacle (legacy from Rev-A; not populated on Rev-B) |
| `X_SW_Slide_SPDT_SSK12D07VG5.kicad_mod` | SPDT slide switch |
| `ETH_Zurich_Logo.kicad_mod` | ETH Zürich logo on F.SilkS |
| `GHE_Logo.kicad_mod` | Global Health Engineering logo on F.SilkS |

## Registration

Registered via `../fp-lib-table` at the parent `hardware/` level —
opening the project loads it automatically.

## Logo footprints

`ETH_Zurich_Logo.kicad_mod` and `GHE_Logo.kicad_mod` are generated
from the source PNG / JPG assets in `../scripts/` by
`../scripts/logo_to_footprint.py`. Regenerate them rather than
hand-editing if the source artwork changes; the script enforces the
≥ 0.2 mm minimum feature size required for JLCPCB silkscreen.

## Licensing — important

These three footprints have a **different** license from the rest of
the repository:

- `SW_HYP_1TS005F-2500-5001.kicad_mod`
- `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.kicad_mod`
- `X_SW_Slide_SPDT_SSK12D07VG5.kicad_mod`

→ **CC BY-SA 4.0** (see `../../LICENSE-CC-BY-SA-4.0.md`).

All other footprints in this folder are CERN OHL 2.0 Permissive (see
`../../LICENSE-CERN-OHL-2-PERMISSIVE.md`).

If you redistribute the three CC BY-SA footprints separately from the
project, you must comply with the share-alike clause. Bundling them
with the rest of the project as part of normal use is fine — the
license boundary only matters at extraction.

## Adding a footprint

1. Create the footprint in the KiCad Footprint Editor and save it here.
2. Verify the courtyard, fab, and silk layers are populated.
3. If the part is not in `../3dmodels/`, link a 3D model so the
   board's `.step` export stays correct.
4. If the footprint is derived from a vendor-licensed source with
   restrictions, document the license in this README.
