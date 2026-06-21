# TAPRX-888 — Consolidated Schematic Review (rev 3)

**Target:** `github.com/TAPR/TAPRx888`, KiCad 9.0 project — files `TAPRX-888.kicad_sch` (root, 120 symbols), `refclk.kicad_sch`, `Front_End.kicad_sch`.

**References used in this review**
- SuperSpeed Explorer Kit schematic (Cypress CYUSB3KIT-003, doc 630-60194-01) — authoritative FX3 ball map.
- Infineon **AN70707** — FX3/FX3S/SX3 Hardware Design Guidelines and Schematic Checklist (001-70707 Rev.*Q).
- **ringof/rx888-firmware** (`SDDC_FX3/radio/rx888r2.c`) — authoritative GPIO→function map.
- TAPR/TAPRx888 **closed issues** #1–#13 (+ open PR #4).
- Version diff against `TAPRX-888 v0.3-reannotated.zip`, `v0.1.zip`, and the dated backup.

---

## 0. Read this first — method and its limits

This review is built by parsing the schematic *source* (S-expression netlist extraction), not by running KiCad's own ERC/netlister. That distinction matters:

- **What is reliable here:** device ball/pin *identities* (cross-checked against the Explorer Kit and AN70707), the component inventory, the presence/absence of parts, and **differences between schematic versions** (the same tool applied to two files cancels its own quirks).
- **What is NOT fully reliable:** absolute net membership. The parser demonstrably misses some connections — it reports AVDD (A7), U3RXVDDQ (A2), and U3TXVDDQ (B5) as *unconnected*, which cannot be literally true — and it can link two wires that merely cross without a junction. So any single "net X is tied to Y" claim below is a **flag to confirm in eeschema/ERC**, not a proven fault.

**Bottom line up front:** the only item that could damage hardware (FX3 power/ground) and a cluster of FX3 control-pin connections *parse as wrong* in the current files, and they line up with problems the TAPR team already filed as issues. But because the parser has shown artifacts, the responsible conclusion is **"open U11 in KiCad, run ERC, and verify against the Explorer Kit page-4 power sheet + AN70707 Table 3"** — not "the board is broken." This document gives the exact nets to check.

---

## 1. Architecture (confirmed-good)

HF-only RX-888-class SDR: `SMA → bypassable LC filter (J6–J9) → AD8370 VGA → LTC2208 16-bit ADC → CYUSB3014 (FX3) GPIF II 16-bit → USB 3.0`, clocked by Si5351A (U20) + 27 MHz TCXO (X1) with an auto-switching external-reference path (U.FL J10 → TLV3501 comparator → NC7SV157 muxes → SN65LVDS1 sample-clock buffer). SPI flash (MX25L3233F, U9) for boot; I²C to the Si5351; 19.2 MHz oscillator (U10) for the FX3 reference. Per-domain LDOs, Schottky-coupled 3.3 V pair, 3.3 V pre-reg into the 1.2 V (AMS1117-1.2). USB port has SP3011 TVS + PESD5V0 ESD. Generous decoupling (33×0.1 µF + 5×10 µF + 4×22 µF on root). No architectural concerns — sensible, buildable topology.

---

## 2. FX3 ball identities — TRIPLE-CONFIRMED (this part is certain)

The TAPRX-888 FX3 symbol's pin **names** match the Cypress silicon exactly. Verified against both the Explorer Kit schematic (page 4) and AN70707 Table 3 / power figure:

| Function | Balls | Voltage |
|---|---|---|
| VDD (core) | B10, C3, E9, F11, H1, J11, L5, L7 | **1.2 V** |
| AVDD | A7 | 1.2 V |
| U3RXVDDQ / U3TXVDDQ | A2 / B5 | 1.2 V |
| CVDDQ | B6 | 1.8 or 3.3 V (= clock-input voltage) |
| VSS (ground) | A8, B7, B8, B9, D8, E2, G1, G11, K3, K4, L1, L2, L3, L6, L11, A1 | GND |
| VIO1 / VIO2 / VIO3 / VIO4 / VIO5 | L9,H11 / F1 / E3 / B1 / C11 | 1.8–3.3 V |
| VBUS / VBAT | E11 / E10 | 3.3–5 V |
| CLKIN / XTALIN / XTALOUT | D7 / C6 / C7 | — |
| RESET_N | C5 | — |
| FSLC0 / FSLC1 / FSLC2 | B2 / B4 / E6 | strap |
| R_USB2 / R_USB3 | C8 / B3 | — |
| PCLK (GPIF clock, GPIO16) | J6 | — |

Because these identities are certain, any net that connects them incorrectly is a real problem — which is what makes Section 3 worth checking carefully.

---

## 3. Nets that parse as WRONG in the current schematic (verify in ERC)

Every item below is present **identically** in the current branch, the v0.3-reannotated zip, and the dated backup (see Section 5).

**3.1 FX3 power / ground — the only potential board-killer.**
As parsed, the 1.2 V-core balls (B10, C3, E9, F11, H1, J11, L5, L7) **plus VIO1/VIO2** share a net with a **GND** power port, while the ground balls (B8, B9, K3, K4, L1, L3, L6, L11) share a net with a **positive-rail** power port (a port whose value is `+1V2` but whose pin name is `+3V3` — itself an inconsistency to fix). If real, this inverts core power and ground and would destroy the FX3/regulator on power-up. *This is the #1 thing to confirm.* (Caveat: the parser also reported AVDD/U3VDDQ as floating, which is certainly an artifact, so a crossing-wire false-merge on these power nets is possible — confirm visually.)

**3.2 FX3 clock input.** The 19.2 MHz oscillator (U10) net `CLKIN` lands on **ball C1 (GPIO54)**, not a clock pin; the real **CLKIN ball D7** is on the **SPI_SSN** net; **XTALIN (C6)** parses as floating. As drawn the FX3 has no valid reference clock. Per AN70707 §5: drive **CLKIN (D7)** and strap **FSLC=100**, *or* use a crystal on XTALIN/XTALOUT with **FSLC=000**; set **CVDDQ** to the clock-input voltage; no series R on XTAL pins.

**3.3 FSLC[2:0] strapping.** FSLC1 (B4) → **SPI_MOSI**, FSLC2 (E6) → **SPI_MISO**, FSLC0 (B2) floating. FSLC must be tied to a defined combination (AN70707 Table 7). Tying them to live SPI signals leaves the clock-mode undefined.

**3.4 RESET.** RESET_N (C5) parses onto an **ID5**-labeled net rather than the RC + pushbutton reset. (Compare closed issue #5, "move ID3/ID4/ID5 to other GPIO.")

**3.5 SPI flash chip-select.** Flash CS (U9 pin 1) parses onto the **SPI_SCK** net instead of a chip-select/SSN. Also confirm AN70707 §8.4: 2 kΩ pull-down on MISO, no pull-ups on MISO/MOSI.

**3.6 USB reference resistors.** R_USB2 (C8) parses onto **VBUS**; R_USB3 (B3) parses straight to **GND**. AN70707 §12.1 requires **C8 → 6.04 kΩ 1% → GND** and **B3 → 200 Ω 1% → GND** (parts R13=6.04 k, R14=200 exist — confirm they land on C8/B3). Also confirm 0.1 µF AC-coupling caps on the SS_TX pair.

**3.7 ADC control (LTC2208).** SHDN (pin 19) and DITH (pin 20) parse to GND. Confirm against the LTC2208 datasheet and the firmware map (§4) — DITH/SHDN/RAND/PGA should be driven or strapped intentionally, not accidentally grounded. (Compare closed issue #13, "SHDN should be driven by FX3.")

---

## 4. Firmware GPIO map (ringof/rx888-firmware) — what the control nets must match

From `SDDC_FX3/radio/rx888r2.c`:

| GPIO | Function |
|---|---|
| 17 | ATT_LE |
| 18 | BIAS_VHF |
| 19 | BIAS_HF |
| 20 | RANDO (ADC RAND) |
| 21 | LED_BLUE |
| 24 | PGA |
| 26 / 27 | ATT_DATA / ATT_CLK |
| 28 | SHDWN (ADC SHDN) |
| 29 | DITH (ADC dither) |
| 35 | VHF_EN |
| 38 | VGA_LE |

Whatever the schematic settles on for these control nets must match this map, **or** the firmware fork must be updated for the TAPRX-888. Note the board has no VHF path, so BIAS_VHF/VHF_EN are candidates to repurpose (cf. the design's reuse of GPIO35 for clock select).

---

## 5. Version diff result (answers "are the fixes in a different file?")

| Comparison | FX3 nets | Verdict |
|---|---|---|
| current vs **v0.3-reannotated.zip** | all 15 identical | same electrical design; differs only in refdes/layout metadata (same 120 parts, same values) |
| current vs **dated backup** (2026-06-03) | all 15 identical | same design |
| current vs **v0.1.zip** | not comparable | v0.1 is the older "x-888" lineage with a different symbol set/designators |

**Conclusion:** the repo contains a single current design (current ≡ v0.3-reannotated ≡ backup). The closed-issue fixes are **not** sitting in a separate version — so either they were never committed to these schematic files, or the parser is misreading the common version. The diff cannot distinguish those two; only ERC can.

---

## 6. Mapping to the closed issues

| Issue | Topic | What the current files parse as |
|---|---|---|
| #8 CRITICAL | AVDD A7 → 1.2 V | VDD-core balls share a net with a GND port; A7 parses isolated → **inconclusive, verify** |
| #12 | Oscillator / FSLC / CLK-XTAL | osc→GPIO54, CLKIN(D7)→SPI_SSN, FSLC1/2→SPI lines → **appears unresolved** |
| #5 | Move ID3/ID4/ID5 | RESET(C5) on an ID5 net → **appears unresolved** |
| #6 | USB2/USB3 1% resistors | R13=6.04 k, R14=200 present; C8→VBUS, B3→GND look off → **verify** |
| #13 | SHDN driven by FX3 | SHDN(19) parses to GND → **verify** |
| #11 | GPIF series resistors | R9–R12 22 Ω arrays present → **appears addressed** |
| #10 | VDDQ bulk/ferrites | not cleanly traceable → **verify per AN70707 Table 3** |
| #9 | PMODE up/down/Hi-Z | PMODE0/1 have resistor pairs; PMODE2→GPIO14 → **partially addressed** |
| #1,#2,#3,#7 | test points, clock test port, EEPROM boot, pin review | not separately verified |

---

## 7. AN70707 checklist deltas to confirm

- **Decoupling (Table 3):** VDD group 22 µF + per-pin 0.01/0.1 µF; AVDD 2.2 µF; **U3RxVDDQ & U3TxVDDQ each 22 µF** (USB3 PHY inrush is up to ~800 mA for ~10 µs — this bulk is not optional); CVDDQ, VIO1–5, VBUS per table.
- **Clocking (§5):** CLKIN+FSLC=100 *or* crystal+FSLC=000; CVDDQ = clock-input voltage; no series R on XTAL pins; crystal within 2 cm, no vias on XTAL traces.
- **GPIF (§6):** 22 Ω series on all data/PCLK lines, length-matched <500 mil; GPIO16 (J6) = PCLK; PMODE[2:0] = GPIO[32:30] strapped at boot.
- **USB (§7, §12):** OTG_ID to GND only if dual-role (leave open for device-only); R_USB2=6.04 kΩ on C8, R_USB3=200 Ω on B3 (both 1% to GND); SS_TX AC caps 0.1 µF; 90 Ω diff, <3 in, SP3010 ESD near connector.
- **SPI (§8.4):** 2 kΩ pull-down on MISO, no pull-ups on MISO/MOSI.
- **Booting (§9):** PMODE[2:0] 10 kΩ up/down/Hi-Z options for SPI-flash boot.

---

## 8. Recommended next steps (in order)

1. **Open `TAPRX-888.kicad_sch` in KiCad and run ERC.** This is authoritative and settles every Section 3 flag in minutes.
2. **Verify U11 against the Explorer Kit page-4 power sheet** ball-by-ball using the Section 2 table — power/ground first (the only potential board-killer), then CLKIN/XTALIN/FSLC, RESET, flash CS, and R_USB2/R_USB3.
3. **Fix the `+1V2` power-port whose pin name reads `+3V3`** (and any similar) so ERC and net names are trustworthy going forward.
4. **Reconcile control-net assignments with the firmware GPIO map** (Section 4), or plan the firmware fork.
5. **Confirm decoupling/USB-reference values against AN70707** (Section 7).

If ERC comes back clean on the Section 3 nets, then my parser's flags there were artifacts (the AVDD-floating result shows it makes mistakes) and the board is in much better shape than this document's flags suggest. Either way, the ball-identity table (Section 2), the firmware map (Section 4), the version-diff conclusion (Section 5), and the AN70707 deltas (Section 7) stand on their own.
