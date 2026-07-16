# TAPRX-888

A simplified, **HF-only** software-defined radio (SDR) receiver based on the
**RX-888** — a proof-of-concept on a larger 6-layer board with improved thermal
and RF layout.

The KiCad project lives at the repository root (`TAPRX-888.kicad_pro` /
`.kicad_sch` / `.kicad_pcb`). **KiCad 10.0** is the project baseline.

## Features

- HF-only — no VHF up/down converter
- Larger PCB, 6-layer
- No bottom-side components
- 0603 passive components
- Improved thermal layout
- Improved RF input filter(s) (bypassable)
- External reference clock input, auto-switching
- Attenuated filter-bypass injector port (used for timesync)
- SPI boot prom. configurable as USB boot, SPI boot, SPI boot with USB fallback.

Please see the schematic and layout documents for details.

## Core devices

| Function | Part |
|---|---|
| ADC | LTC2208 (16-bit) |
| Clock generator | Si5351 |
| USB3 controller | EZ-USB FX3 (CYUSB301x) |
| SPI boot flash | MX25L3233F |

## Repository & branches

- **`dev`** — integration branch and the repository default; day-to-day work
  lands here.
- **`main`** — tagged, released board revisions.
- **`design`** — where the schematic and PCB are edited (one person at a time,
  because KiCad layout files can't be merged).

## Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the full workflow. In short:

- Design edits (schematic / PCB / libraries) happen one person at a time on the
  **`design`** branch.
- Everything else (CI, design rules, BOM tooling, docs) is a short **`dev-*`**
  branch opened as a pull request into **`dev`**.
- **`dev` → `main`** (tagged) is a release, cut by consensus.
- ERC and DRC run in CI as the shared source of truth.

## Reference documents

Device datasheets (LTC2208, Si5351, EZ-USB FX3, MX25L3233F) and RX888 reference
material are on the [project wiki → Reference Documents](https://github.com/ringof/TAPRx888/wiki/Reference-Documents).
