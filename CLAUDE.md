# CLAUDE.md — Working Agreement for `TAPRX-888`

Guidance for Claude (and any agent) working in this repository. This is a
**KiCad hardware project**, not a software codebase — the "code" is a schematic,
a PCB layout, and a component library, and the "build" is a set of
manufacturing outputs produced by `kicad-cli`.

## Project

TAPRX-888 is a simplified, HF-only software-defined radio (SDR) receiver based
on the **RX-888**. It is a proof-of-concept design: HF-only (no VHF up/down
converter), on a larger **6-layer** PCB with no bottom-side components and 0603
passives, aimed at improved thermal and RF layout. Notable features: improved,
bypassable RF input filtering; an **external reference-clock input with
auto-switching**; an attenuated filter-bypass injector port (for timesync); and
an SPI boot PROM configurable as USB boot, SPI boot, or SPI boot with USB
fallback.

Core devices: **LTC2208** 16-bit ADC, **Si5351** clock generator, Infineon
**EZ-USB FX3 (CYUSB301x)** SuperSpeed USB3 controller, and an **MX25L3233F**
SPI flash. Datasheets for all of these live in `Reference manuals/`. Design
review notes and open issues are captured in the two `TAPRX-888_*review*.md`
documents at the repo root — read them before making design-touching changes.

## Repository layout

The active KiCad project lives in the **`TAPRX-888 KiCad/`** subdirectory (note
the space in the path — quote it in every shell/`kicad-cli` command).

- `TAPRX-888 KiCad/TAPRX-888.kicad_pro / .kicad_sch / .kicad_pcb / .kicad_prl` —
  the design. The schematic is **hierarchical**: `TAPRX-888.kicad_sch` is the
  root sheet and pulls in `Front_End.kicad_sch` and `refclk.kicad_sch`. Run ERC
  against the root sheet.
- `TAPRX-888 KiCad/fp-lib-table` / `sym-lib-table` — project-local library
  tables (they use `${KIPRJMOD}`; keep paths relative).
- `TAPRX-888 KiCad/Library.kicad_sym` + `Library.pretty/` — the project-local
  symbol library and footprints.
- `TAPRX-888 KiCad/production/` — generated BOMs (`bom.csv`, JLC BOM).
- `Reference manuals/` — device datasheets and reference schematics.
- `JLC Parts Details including MFG and MPN.txt` — MFG/MPN mapping for assembly.

Historical/reference material — do **not** edit these as the live design:
`TAPRX-888 v0.1/` (an earlier snapshot) and `WB6CXC previous work/` (prior
review archives).

**KiCad 10.0** is the project baseline (latest stable 10.0.4). The committed
files are already in the v10 format (`version 20260206`) — no format migration
is pending. Author changes with KiCad 10.

## Working agreement

- **Planning first.** For any multi-step change, write/update a short plan and
  get approval before implementing.
- **Commit & push only with explicit approval.** Never commit or push without
  being asked to.
- **Branch discipline.** `main` is the default branch. Do work on feature
  branches and open a PR into `main`. **Authorization to do work is NOT
  authorization to create a branch** — do not create a branch unless the user
  names it. Unrelated fixes go on the current branch as separate commits unless
  directed otherwise.
- **Evidence before claims.** Do not assert a design problem or file an issue on
  untested theory. Back every finding with concrete evidence: a `grep`/file
  read, a datasheet reference, or `kicad-cli` ERC/DRC/BOM output. (Example: the
  6-layer stackup lists `In1..In4.Cu` as **signal** layers — confirm claims like
  that by reading the PCB `(layers …)` stanza, not by assumption.) Existing
  observations override untested theory.
- **Change documentation.** Before committing a design-touching change, give the
  user a copy-pastable block with: (1) what changed and why, (2) how to
  regenerate outputs (`kicad-cli` commands), (3) how to validate (which
  ERC/DRC/BOM checks must pass), (4) regression check (re-run the CI check set).
- **No `gh` CLI here.** GitHub operations go through the GitHub MCP tools, not
  `gh`. When batch-filing findings as issues, use those tools (or offer a
  script), not `gh issue create`.

## Design-rule baseline

- Manufacturing capability reference: **JLCPCB, 6-layer process** (the assembly
  BOM targets JLC part numbers, and `fabrication-toolkit-options.json` drives
  the JLCPCB Fabrication Toolkit export). Set and validate DRC rules against it,
  and keep the board settings (`.kicad_pro` `board_design_settings`) in sync.
- There is currently no separate `.kicad_dru`; custom rules, if added, live
  there and must be understood before being changed.

## CI, provenance & releases

Being implemented in this branch. CI runs `kicad-cli` inside the official
`kicad/kicad:10.0` Docker image (the toolchain that matches the file format).

- **PR / branch CI** (gate): **ERC** on the root schematic and **DRC** on the
  PCB. Also generates the schematic PDF, Gerbers/drill, and BOM as downloadable
  artifacts.
- **Release CI** (planned): produces the full fab/design package (Gerbers,
  drill, BOM, pick-and-place, schematic PDF, STEP) and publishes a GitHub
  Release.

| Check | PR / branch | release |
|---|---|---|
| ERC | gate | gate |
| DRC | gate | gate |
| Fab artifacts (PDF / Gerbers / BOM) | artifact | artifact |

## Useful `kicad-cli` commands (KiCad 10)

Paths contain a space, so quote them.

```sh
cd "TAPRX-888 KiCad"
kicad-cli sch erc          TAPRX-888.kicad_sch --output erc.rpt --exit-code-violations
kicad-cli pcb drc          TAPRX-888.kicad_pcb --output drc.rpt --exit-code-violations
kicad-cli sch export pdf   TAPRX-888.kicad_sch --output TAPRX-888-schematic.pdf
kicad-cli sch export bom   TAPRX-888.kicad_sch --output bom.csv
kicad-cli pcb export gerbers TAPRX-888.kicad_pcb --output gerbers/
kicad-cli pcb export drill   TAPRX-888.kicad_pcb --output gerbers/
kicad-cli pcb export pos     TAPRX-888.kicad_pcb --output cpl.csv   # pick-and-place
kicad-cli pcb export step    TAPRX-888.kicad_pcb --output TAPRX-888.step
```

## Reference docs

- `TAPRX-888_consolidated_review_rev3.md` — consolidated design-review findings.
- `TAPRX-888_schematic_Claude_review_rev2.md` — schematic review notes.
- `Reference manuals/` — LTC2208, Si5351, EZ-USB FX3, MX25L3233F datasheets and
  RX888 reference material.
