# 3d — vendored component 3D models (project-local)

3D models for the handful of components that have **no faithful equivalent in
KiCad's bundled 3D libraries**. Everything else resolves against KiCad's stock
models via `${KICAD10_3DMODEL_DIR}` and needs nothing here.

## Why these live in the repo

The board's footprints used to reference 3D models through a **private**
`${TIS}` library (and the deprecated `${KISYS3DMOD}` variable) that exists only
on the original designer's machine. In CI — and on anyone else's checkout —
those paths don't resolve, so the STEP export and 3D renders can't be built
(issue #45).

The fix is a **two-tier** referencing scheme, chosen so a model is *never
missing*:

| Tier | Variable | Resolves because | Used for |
|---|---|---|---|
| Stock | `${KICAD10_3DMODEL_DIR}` | KiCad defines it; the CI image ships the models | standard packages (0603 R/C/L, SOT-23/223, QFN/DFN, SO/MSOP/TSSOP, BGA, headers, diodes, U.FL …) |
| Local | `${KIPRJMOD}/3d/…` | KiCad always sets `${KIPRJMOD}` to the project dir — it points *inside this checkout* | the custom models below |

`${KIPRJMOD}` needs **zero** configuration on any machine and **zero**
provisioning in the CI image: it is wherever the repo is checked out. That is
the whole point — these models travel with the board and can't go missing short
of deleting them from the repo (which a PR review catches).

## Files expected here

Drop each model in as a **STEP** file (`.step`/`.stp`) with the exact name
below — the footprints already point at these paths, so a drop-in "just works"
and the entry flips from *pending* to *present*. STEP is required because the
board **STEP export only consumes STEP-format models** (it ignores `.wrl`).

| File | Footprint | Refs | Part | Source / license | Status |
|---|---|---|---|---|---|
| `Murata2U.step` | `Murata2U` | L8–L14 | Murata LQW-series wire-wound RF inductor | _TBD_ | ⏳ pending |
| `SMA_Jack_EdgeMount_JLC.step` | `SMA_Jack_EdgeMount_JLC_With_Nut` | J1–J4 | Edge-mount SMA jack (JLC) | _TBD_ | ⏳ pending |
| `USB-3.0.step` | `USB-3.0` | J5 | USB 3.0 connector | _TBD_ | ⏳ pending |
| `TCXO-3225.step` | `TCXO-3225` | X1 | Abracon ASTX-H12 TCXO, 3.2×2.5 mm | _TBD_ | ⏳ pending |
| `SMD-2520.step` | `SMD-2520` | U10 | 19.2 MHz oscillator, 2.5×2.0 mm | _TBD_ | ⏳ pending |
| `LED_RGB_SIDE.step` | `LED_RGB_SIDE` | D3 | Side-view RGB LED | _TBD_ | ⏳ pending |
| `BUTTON-4p5X4p5.step` | `BUTTON-4p5X4p5` | B1 | 4.5×4.5 mm tact switch | _TBD_ | ⏳ pending |

Library-only (not placed on the current board, present in `Library.pretty/`):

| File | Footprint | Part | Status |
|---|---|---|---|
| `SMA-RA-Jack.step` | `SMA-RA-Jack` | Right-angle SMA jack | ⏳ optional |

**Before committing any model here**, fill its *Source / license* cell and
confirm the file is redistributable (manufacturer models usually are; a few
carry restrictive EULAs). Provenance lives in the table above.

## Re-enabling STEP + 3D renders in CI

`scripts/build_release.sh` intentionally does **not** build STEP/renders yet:
KiBot aborts if any `(model …)` path is unresolvable, and the `${KIPRJMOD}/3d/…`
files above are still pending. Once the last one lands (and
`scripts/check_3d_models.py` reports all-present), re-enable the `step` /
`render_top` / `render_bottom` outputs there and confirm CI resolves all models.

## Archival note (future)

For long-term archival — capturing the design so it rebuilds identically with no
dependency on KiCad's shipped libraries — the stock models can additionally be
vendored here and the references repointed from `${KICAD10_3DMODEL_DIR}` to
`${KIPRJMOD}/3d/`. Deliberately **not** done now: it duplicates ~140 stock
0603 models the CI image already provides, for bloat the low-risk stock library
doesn't warrant day-to-day.
