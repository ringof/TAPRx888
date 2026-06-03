# TAPRX-888 — Independent Schematic Review (rev 2, schematic-only)

**Source:** `github.com/TAPR/TAPRx888` (KiCad 9.0 project)
**Files evaluated:** `TAPRX-888.kicad_sch` (root, 180 symbols), `refclk.kicad_sch` (Clock, 81), `Front_End.kicad_sch` (filter, 52).
**Method:** S-expression parse of the schematic source → geometric net trace → cross-check against device datasheets only.

> **What changed from rev 1:** The `TAPRX-888 Review-4.pdf` design document describes an *earlier* state of the design, so it has been **excluded entirely** as a source of intent. Every "the doc says X but the schematic does Y" item from rev 1 is withdrawn — specifically the GPIO17/GPIO29 (DITH vs ext-ref) "swap," the XTALIN-vs-CLKIN clock-input intent claim, and the AD8370 GPIO-number mapping. This review now rests only on the schematic itself and on manufacturer datasheets.

> **Scope/limits (unchanged):** This is schematic-only — the PCB layout (`TAPRX-888.kicad_pcb`) was not reviewed. Findings come from parsing the source, not from KiCad's own ERC/netlister, and the custom "X-888" symbol library has unreliable pin *names* (Finding #1), so net-name checks are only partly trustworthy. Items marked **VERIFY** are *discrepancies to reconcile*, not confirmed faults.

---

## 1. Architecture (read from the schematic)

A clean HF-only RX-888-class SDR:

`SMA in → bypassable LC filter (J6–J9 jumpers) → AD8370 VGA → LTC2208 16-bit ADC → CYUSB3014 (FX3) GPIF II 16-bit → USB 3.0`

clocked by a Si5351A (U20) + 27 MHz TCXO (X1) with an auto-switching external-reference path (U.FL J10 → comparator TLV3501 U16 → NC7SV157 muxes U18/U21), and an LVDS sample-clock buffer (SN65LVDS1, U22) to the ADC. SPI flash (MX25L3233F, U9) for FX3 boot; I²C to the Si5351; 19.2 MHz oscillator (U10) for the FX3 reference.

**Strengths visible in the schematic:**
- **Decoupling is generous:** 33× 0.1 µF + 5× 10 µF + 4× 22 µF on the root sheet, plus per-rail bulk and `FBEAD0603` ferrite isolation on the analog/clock 3.3 V feeds and the FX3 1.2 V feed (L5/L6/L7).
- **Per-domain regulation:** separate LDOs for ADC-3V3 (U1), FX3-IO-3V3 (U2), VGA-3V3 (U6 feed), and a low-noise LP5907 (U4, and U14 on the clock sheet). The two main 3.3 V regulator outputs are tied by Schottkys D1/D2 (output-coupling — typical for coordinated startup / current sharing). The 1.2 V (AMS1117-1.2, U5) is fed from a 3.3 V pre-regulator (U3) rather than straight off 5 V, which spreads the dissipation.
- **USB port protection:** SP3011 TVS (U7) + PESD5V0 (Z1); series element on the SuperSpeed pair.
- **FX3 housekeeping present:** RESET RC + pushbutton (B1/R6/R7), PMODE[2:0] boot straps, ID[7:0] straps/LED, JTAG pins broken out.
- **Filter flexibility:** shelf and low-pass sections individually jumper-bypassable; an attenuated injector port is summed in at the filter output (useful for time-sync/ToF injection).

No architectural red flags — this is a sensible, buildable topology.

---

## 2. PRIMARY FINDING — the symbol pin names don't match the wiring

This is the dominant issue and it's purely schematic-internal (no datasheet or doc needed to see the contradiction). The X-888 library symbols carry pin **names** that are inconsistent with how the pins are wired.

Cleanest proof — the **FX3 (U11) power balls**, traced through the regulator (not through power-symbol labels, so this is trustworthy):

| Symbol pin name | Balls (BGA) | Wired to |
|---|---|---|
| `VSS@5,6,7,11,12` | B8, B9, K3, K4, L1, L3, L6, L11 | **U5 output (+1.2 V)** |
| `VDD@1…8` | B10, C3, E9, F11, H1, J11, L5, L7 | **GND** |
| `VIO1`, `VIO2` | F1, H11, L9 | **GND** |

The +1.2 V identity is anchored by tracing to **U5's output pin (AMS1117-1.2)**, independent of any label. So as drawn: balls the symbol calls **VSS** sit on **1.2 V**, and balls it calls **VDD/VIO** sit on **GND**. A pin named `VIO` (an I/O supply) tied to ground is electrically impossible if that ball is truly an I/O supply — so the symbol's name↔ball mapping is provably wrong somewhere.

Two outcomes, and **only a datasheet ballout check tells you which:**
- **Benign:** the symbol *names* are scrambled but each ball was placed on the correct rail by position → netlist fine, fix cosmetics.
- **Catastrophic:** the wiring followed the wrong names → 1.2 V core balls grounded / ground balls on 1.2 V = short on power-up.

**Action (highest priority — only finding that can damage hardware):** Open the FX3 ballout (Infineon 001-52136, 121-ball BGA) and confirm the true function of each ball above. From the datasheet, the 1.2 V-class supplies are VDD (core), AVDD, U3TxVDDQ, U3RxVDDQ; VIO1 (GPIF II I/O) cannot be turned off; VIO5 powers I²C/JTAG; CVDDQ tracks the clock-I/O voltage. For reference, the symbol assigns AVDD/U3RxVDDQ/U3TxVDDQ/CVDDQ to balls A7/A2/B5/B6 — check those land on 1.2 V too. Once corrected, ERC becomes meaningful.

**The same caution applies to U8 (LTC2208) and U6 (AD8370)** — their symbol pin names cannot be trusted at face value either, including the `GPIOxx` names on the FX3 (so refer to balls by BGA coordinate, not by the GPIO name printed in the symbol).

---

## 3. Items to VERIFY (schematic-internal inconsistencies)

Each of these is a contradiction *within the schematic* (a net label vs a symbol pin name) — independent of the now-excluded design doc.

**(a) LTC2208 control pins.** A net **labeled `DITH`** traces to LTC2208 **pin 7**, whose symbol name is `GND_4`; meanwhile the pin the symbol *names* `DITH` (pin 20) traces to GND. So either pin 7 is the real dither/control pin (symbol name wrong) or a control signal is being driven into a ground pin. Walk pins 1 (SENSE), 19 (SHDN), 20 (DITH), 61 (LVDS), 62 (MODE), 63 (RAND), 64 (PGA) against the LTC2208 datasheet and confirm each control net lands on the intended pin and that unused control pins are strapped to a defined level, not floating.

**(b) AD8370 (U6) serial gain interface.** Net labels `VGA_D`, `VGA_CLK`, `VGA_LE` exist, but the VGA's CLK/DATA-named pins (13/14) appear tied to GND in my trace while only LE (pin 12) shows a live connection. This is exactly the kind of result the symbol-naming problem can corrupt, so I won't call it a fault — but **confirm the 3-wire interface (DATA 14, CLK 13, LE 12) is actually driven and not grounded.** If the gain register can't be clocked in, the VGA stays at its power-up gain.

**(c) FX3 clock input.** The `CLKIN` net carries the 19.2 MHz oscillator (U10) to the FX3. Because the FX3 distinguishes XTALIN/XTALOUT (crystal) from CLKIN (external clock) and the symbol names are unreliable, **confirm (i)** the oscillator reaches the ball that is genuinely the clock input, and **(ii)** the **FSLC[2:0] straps** select the matching mode (datasheet: `000` = 19.2 MHz crystal, `100` = 19.2 MHz external CLK). A single-ended oscillator into XTALIN while strapped "crystal" is the fragile path; CLKIN + FSLC=`100` is the datasheet-blessed one.

**(d) FX3 unused inputs.** Confirm CLKIN_32, unused VIO domains, OTG_ID, R_USB2/R_USB3 reference resistors, and the JTAG pins are terminated per the FX3 hardware checklist — I couldn't clear all of these through the symbol-name noise.

---

## 4. Smaller notes

- **Fix the symbols, then run ERC.** Today ERC would be buried in false power-pin/unconnected errors from the bad names, masking anything real. This is the single highest-leverage step.
- **Work the Cypress FX3 hardware checklist (AN70707)** line-by-line for U11 (power sequencing, VIO1 always-on rule, CVDDQ voltage, VBUS/VBATT, reference resistors).
- **Cross-reference the public RX-888 MkII schematic** for the FX3 and LTC2208 connections — it's a proven reference and will settle the symbol-name questions quickly.
- **ADC data-bus damping arrays (R9–R12, `R-22 0402x4`):** confirm orientation (which side is FX3 vs ADC) so the DA bus isn't transposed.
- **Time-sync injector network:** sanity-check the attenuator values place the injected level sensibly relative to the antenna path (relevant once the symbol issues are cleared).

---

## 5. Bottom line

The topology is solid and buildable. The blocker is the **symbol library**, whose pin names are demonstrably inconsistent with the wiring — that both prevents meaningful ERC and leaves three connectivity questions (FX3 power balls, ADC/VGA control pins, FX3 clock) that can't be closed from the source alone. Correct the symbol pin names to match datasheets, re-run ERC, and walk U11/U8/U6 against AN70707 and the datasheet pinouts. **Start with the FX3 power-ball check (Finding #2)** — it's the only item that could damage hardware.

If you tell me whether to treat the **symbol pin names or the wiring** as ground truth, I can dump exact wire-level connectivity around any block (FX3 power, VGA control, Si5351 clock-switch) and give a definitive verdict on each.
