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

| File | Footprint | Refs | Part | LCSC # | License | Status |
|---|---|---|---|---|---|---|
| `Murata2U.step` | `Murata2U` | L8–L14 | Wire-wound RF inductor, 1008 (120–820 nH) | `C162664`, `C701161`, `C2044072`, `C2043109` ¹ | _TBD_ | ⏳ pending |
| `SMA_Jack_EdgeMount_JLC.step` | `SMA_Jack_EdgeMount_JLC_With_Nut` | J1–J4 | Edge-mount SMA jack w/ nut | `C2874826` ² | _TBD_ | ⏳ pending |
| `USB-3.0.step` | `USB-3.0` | J5 | USB 3.0 connector | `C2895032` | _TBD_ | ⏳ pending |
| `TCXO-3225.step` | `TCXO-3225` | X1 | 27 MHz TCXO, 3.2×2.5 mm | `C5203549` (alt `C46598427`) | _TBD_ | ⏳ pending |
| `SMD-2520.step` | `SMD-2520` | U10 | 19.2 MHz oscillator, 2.5×2.0 mm | `C49304731` | _TBD_ | ⏳ pending |
| `LED_RGB_SIDE.step` | `LED_RGB_SIDE` | D3 | Side-view RGB LED | `C389528` | _TBD_ | ⏳ pending |
| `BUTTON-4p5X4p5.step` | `BUTTON-4p5X4p5` | B1 | 4.5×4.5 mm tact switch | `C410371` | _TBD_ | ⏳ pending |
| `SP3011.step` | `SP3011` | U7 | Littelfuse SP3011-06UTG TVS array, UDFN-14 (~3.5×1.35 mm) | `C207281` | _TBD_ | ⏳ pending |

¹ One model body covers all seven (identical 1008 package, differing inductance):
L8 180 nH `C162664`; L9/L12 820 nH `C701161`; L10/L11 120 nH `C2044072`;
L13/L14 150 nH `C2043109`. Grab any one's STEP.
² Correct part for all four is `C2874826`; J2–J4 currently carry the wrong
`C914558` in the BOM (tracked in #63). A single model body fits all four.

The LCSC number is the fastest route to a STEP: the part's LCSC/JLCPCB page (or
its EasyEDA model) almost always has one. Fill the **License** cell — and confirm
redistribution — before committing each model.

Library-only (not placed on the current board, present in `Library.pretty/`):

| File | Footprint | Part | Status |
|---|---|---|---|
| `SMA-RA-Jack.step` | `SMA-RA-Jack` | Right-angle SMA jack | ⏳ optional |

**Before committing any model here**, fill its *Source / license* cell and
confirm the file is redistributable (manufacturer models usually are; a few
carry restrictive EULAs). Provenance lives in the table above.

## 3D model ↔ footprint alignment policy

Who owns the alignment correction depends on which side we control. The rule:
**where you do *not* control the geometry (a KiCad stock model, or a KiCad stock
footprint), correct in the footprint's model transform and leave the STEP
untouched; where you control *both* (custom footprint + custom model), make them
seat at identity by construction.**

| | **KiCad standard footprint** | **Custom footprint** |
|---|---|---|
| **KiCad standard model** | **(1)** Aligns at identity by design. The transform **must** be `offset 0/0/0`, `rotate 0/0/0`, `scale 1/1/1`; strip any stray transform that crept in. | **(2)** Never modify the stock STEP (it's shared and gets overwritten on library updates). Align in **Footprint Properties → 3D Models** (offset/rotate). |
| **Custom / vendor model** | **(3)** Never modify the stock footprint. Align in **Footprint Properties** (offset/rotate) — or fix the model's origin in the STEP. | **(4)** We own both, so make them align at **`offset 0/0/0`, `rotate 0/0/0`**: author/export the STEP with its origin and orientation matching the footprint (which sits at the standard origin). No transform hacks. |

Notes:
- **`scale` is always `1/1/1`.** A correct STEP is authored in real millimetres.
  Any non-unity or anisotropic scale is a hack forcing a wrong/mis-sized model to
  fit — fix the model or the mapping, don't scale.
- Alignment is a **footprint-level** property: apply a correction to *every*
  instance of a footprint type (keep them uniform) and to the `Library.pretty/`
  source, not to one placed instance.
- **How this project maps on:** the board's stock models sit on **custom** TIS
  footprints → **case 2** (align via footprint transform, STEP untouched — this is
  what the per-footprint calibration pass does). The custom parts in the table
  above are custom model **on** custom footprint → **case 4** (their footprint
  transform is reset to identity; author the vendored STEP to seat there).

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
