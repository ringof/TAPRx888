# TAPRX-888
A simplified SDR, based on the RX-888.

The KiCad project lives at the repository root (`TAPRX-888.kicad_pro` /
`.kicad_sch` / `.kicad_pcb`).

Proof-of-concept design

HF-only, no VHF converter

Larger PCB, 6-layer

No bottom-side components

0603 passive components

Improved thermal layout

Improved RF input filter(s) (bypassable)

External reference clock input, auto-switching

Attenuated filter-bypass injector port (used for timesync)

SPI boot prom. configurable as USB boot, SPI boot, SPI boot with USB fallback.

Please see schematic and layout documents.

## Reference documents

Device datasheets (LTC2208, Si5351, EZ-USB FX3, MX25L3233F) and RX888 reference
material are on the [project wiki → Reference Documents](https://github.com/ringof/TAPRx888/wiki/Reference-Documents).
