# CoffeeRoast RevA.1 JLCPCB order handoff

Status: current as of the 2026-07-07 no-J1-J4 PCBA cleanup + fresh JLC gerber-only upload: J1-J4/C3697 must **not** be selected in Component Placement; they are hand-solder pads only. The JLC PCB upload now uses a Gerber/drill-only ZIP with no embedded assembly/DNP CSVs, and PCBA uses separate clean 19-designator BOM/CPL files excluding J1-J4. No payment/order was placed; checkout/save-to-cart still requires user JLC login/security step.

## What was completed

- Local ZIP integrity verified with `unzip -t` after ESP32 bottom-label cleanup.
- KiCad full DRC re-run after ESP32 bottom-label cleanup: 0 DRC violations, 0 unconnected pads, 0 footprint errors.
- Fresh Gerber/drill-only package uploaded to JLCPCB after discovering J1-J4/C3697 still appeared in Component Placement.
- Fresh JLC gerber analysis returned `head=ok`; Gerber upload ZIP contains no assembly CSV and no DNP/reference CSV.
- Dedicated PCBA files generated with exactly 19 designators and no `J1`, `J2`, `J3`, `J4`, or `C3697`.
- JLC detected:
  - Layers: 2
  - Board size: 160.0 mm x 100.0 mm
  - Gerber result: 0
- KiCad-Happy PCB pre-fab pass after changes: 0 active-stage errors, 0 active-stage warnings, 6 info findings.
- KiCad-Happy EMC score after changes: 79/100.
- KiCad-Happy-driven layout changes applied:
  - 3 top-side global fiducials (`FID1`-`FID3`).
  - 3 bottom-side global fiducials (`FID4`-`FID6`).
  - B.Cu `GND_B_CU_KICAD_HAPPY` ground pour following the rectangular board outline.
  - USB-C receptacle `J5` moved to the normal right board edge (`x=154`, footprint bbox right ≈ `159.78 mm`) with no notch/cutout.
  - `TPRESET1`: tweezer pads for `EN` to `GND` reset.
  - `TPBOOT1`: tweezer pads for `BOOT` to `GND` bootloader/flash mode.
  - `TPSSR1`: SSR OUT measurement pads for `+5V` and `SSR_NEG`.
  - ESP32 GPIO breakout row labels changed from `IOxx` to `GPIOxx` (`GPIO3`, `GPIO46`, `GPIO9`, `GPIO10`, `GPIO48`, `GPIO45`).
  - Footprint-generated F.SilkS outlines moved to F.Fab to reduce `silk_over_copper` warnings from 69 to 0 while keeping functional board labels.
  - Vias raised to 0.55 mm / 0.30 mm where needed for 0.125 mm annular ring.
  - +24V_RAW and +24V_FUSED widened to 0.60 mm; SSR_NEG widened to 0.35 mm where DRC-clean.
  - C6/C7 100 nF 0603 local decoupling added and included in BOM/CPL.
  - U3 +3V3 thermal/output via mesh added.

## Files

Superseded upload package:

`production/partial-smd-pcba/CoffeeRoast-Control-RevA1_partial_smd_pcba_package.zip`

Current Gerber-only JLC upload package (use this for PCB quote upload; it intentionally contains no assembly/DNP CSVs):

`production/jlc-current-no-j1j4/CoffeeRoast-Control-RevA1_JLC_GERBER_ONLY_no_assembly_csv.zip`

Current PCBA BOM/CPL files to upload separately in the SMT step:

- `production/jlc-current-no-j1j4/assembly/bom_jlc_pcba_19_no_j1_j4.csv`
- `production/jlc-current-no-j1j4/assembly/cpl_jlc_pcba_19_no_j1_j4.csv`

Do not upload `dnp_hand_solder.csv` to JLC; it is a local reference only.

Expanded PCBA candidate package if the user wants to try assembling more parts, still excluding `J1-J4`/`C3697`:

`production/jlc-expanded-pcba/CoffeeRoast-Control-RevA1_EXPANDED_PCBA_CANDIDATES_NO_J1J4.zip`

Recommended first expanded attempt after an off-board placement preview:

- BOM: `production/jlc-expanded-pcba/assembly/bom_jlc_pcba_31_all_real_no_j1_j4_manual_select.csv`
- CPL: `production/jlc-expanded-pcba/assembly/cpl_31_all_real_kicad_official_negative_y_no_j1_j4.csv`

If that placement is still off-board, replace only the CPL with the `raw_top_left_positive_y` variant, then the `jlc_bottom_origin_y_flipped` variant. Use only one CPL at a time.

Local selected-parts references:

- `production/selected_parts.md`
- `production/selected_parts.csv`

## JLC upload identifiers

These are not passwords, but treat them as project/order identifiers. The first three IDs are the latest successful JLC gerber-only upload after the no-J1-J4 PCBA cleanup. Older IDs refer to superseded/stale uploads and must not be used for checkout.

- Current upload file ID / uploadNum: `0fb595726dc344d08a0c93a965b2918a`
- Current JLC fileSystemAccessId from upload API: `8762676467983626240`
- Current JLC technologyDiscernRecordNum from analysis: `890a204767ee476a8a7d48bfb4125242`
- Superseded 2026-07-07 upload file ID: `b79fcd4656504de2b88788e326fa1e3f`
- Superseded 2026-07-07 upload file ID: `ec94da6785004292b28d694fd487d497`
- Superseded 2026-07-06 upload file ID: `da1c744795744206b9dbcd9eb9e53572`
- Superseded 2026-07-06 upload file ID: `6bc7198bdb4a426a94c082b9e99f1e42`
- Superseded 2026-07-06 upload file ID: `2e2dcb33e319420daa2fc07c14095cf5`
- Superseded 2026-07-06 upload file ID: `1d614f325e034b4eabd03bdfc3f4ce16`
- Superseded 2026-07-06 upload file ID: `5589608d0e9142d9beb6178229709b01`
- Superseded 2026-07-06 upload file ID: `33c7e1703ab74cb1af36d366eef95360`
- Superseded 2026-07-06 upload file ID: `b456f7c68a214c6f8a26de127edc7853`
- Superseded 2026-07-05 upload file ID: `f0faa4c0862947d1b4b273692f1dd94c`

Resume URL after login:

`https://cart.jlcpcb.com/quote?uploadNum=0fb595726dc344d08a0c93a965b2918a`

Use the URL above after JLC login/security to continue the quote. Before payment, verify the fresh JLC preview, then upload/check BOM/CPL and PCBA placement in the logged-in flow. API/browser login attempts with stored credentials reached JLC's Passport `/login` endpoint but returned code `103324` / `Validation failed, fallback retry is required`, which corresponds to the visible reCAPTCHA security verification; continue only after a legitimate authenticated session exists.

## Recommended JLC settings

PCB:

- Product: Standard PCB/PCBA
- Base material: FR-4
- Layers: 2
- Dimensions: should auto-detect 160 x 100 mm
- Quantity: 5 boards
- Thickness: 1.6 mm
- Color: Green or default
- Surface finish: LeadFree HASL or ENIG if price is acceptable
- Outer copper: 1 oz
- Electrical test: Flying Probe Fully Test
- Mark on PCB: Remove Mark if possible

PCBA:

- Enable SMT Assembly
- Side: Top side only
- Use `assembly/bom_smd_partial.csv`
- Use `assembly/cpl_smd_partial.csv`
- Assemble only the 19 BOM positions in `bom_smd_partial.csv`
- If possible, order 5 PCBs but only 2 assembled

Do not assemble / leave DNP:

- U5 USB ESD
- D2/D3 TVS
- C5 thermocouple filter
- J1-J4 large hand-solder pads / no connector assembly
- F1 fuse holder
- D1 fan diode
- Q1 fan MOSFET
- U3/U4 regulators/modules
- C4 input electrolytic
- SW1/SW2 buttons
- all TP/PAD debug pads

## Manual UI checks before paying

- Confirm U1 ESP32-S3 orientation and antenna keepout preview.
- Confirm U2 MAX6675 pin-1 orientation.
- Confirm J5 USB-C orientation.
- Confirm Q2 SOT-23 orientation.
- Confirm all JLC supplier/C-codes still resolve:
  - C2913201, C16030, C319148, C8545, C17408, C149504, C17414, C17594, C27834, C15850, C49678.
- If any part is unavailable or preview looks wrong, mark that part DNP and hand-solder later.

## Current blocker

The site redirected to JLCPCB login before I could continue into cart/checkout. The assistant stopped before credentials/payment.
