# Mechanical — enclosure & PCB end plates

The mechanical package for the TAPRX-888: the enclosure model and the end-plate
boards. It lives in **this repo, not a separate one**, on purpose — see below.

## Layout

```
mechanical/
  enclosure.step          # the case model — the EE↔ME interface artifact
  endplate-front/         # a standalone KiCad project (front panel)
  endplate-rear/          # a standalone KiCad project (rear panel)
```

## Enclosure model

`enclosure.step` is the [JLCMC split aluminium box][box] (`K70-8838-H7`,
88 × 38 mm cross-section), **shortened from the stock 120 mm to 100 mm** to match
the board, with the **stock end plates removed** so the fabricated PCB plates
take their place. It's a **two-piece** model (the two clamshell halves) and is
the EE↔ME interface artifact — the end-plate outline and its M3 corner
mounting-hole pattern (Ø3.4 at ±41, ±14.21 from centre) were taken directly from
its end profile. Verified: 88 × 38.02 × 100 mm, 2 solids.

[box]: https://jlcmc.com/product/b/U01/BR9272/aluminum-box-%28jlc%29-88*38*120mm-split

Each end plate is its **own** self-contained KiCad project (its own
`fp-lib-table` / `sym-lib-table`); the root `TAPRX-888` board is untouched. The
end plates are **non-functional PCBs** — Edge.Cuts, connector cutouts, mounting
holes, and silkscreen (labels + the TAPR / HamSCI / TIS logos) — fabricated in
place of the blank panels the enclosure ships with.

## Why in this repo, not a separate one

The end plates are **mechanically coupled** to the main board: their cutouts have
to track the board's connector positions. Keeping them here means a connector
move and its matching cutout move land as **one atomic, reviewed commit**, and
they version and travel together. A separate repo would split that into two
places to keep in sync by hand — exactly the drift we're avoiding.

## Versioning — board and plates are separate lanes

On **`main`** the two ship independently: a `mechanical/` change never bumps the
board's `vX.Y` (`main-release` is scoped to the root board), and the end plates
have their own **`endplates-vX.Y`** release lane (`endplate-release.yml`). On
**`dev`** the `v0.x` **pre-release is a combined snapshot** — a board, end-plate,
or mechanical change cuts/refreshes it, bundling the board package, both plate fab
packages, and the mechanical assembly. See `docs/RELEASE_STRATEGY.md`.

## The board STEP is the interface

Mechanical design works from the board's exported **STEP** (board outline,
thickness, connector positions, component heights, mounting holes). The 3D models
are now resolved (all vendored in-repo, see `3d/README.md`), so `main-release`
publishes the fully-populated board STEP as a **standalone release asset**
(`TAPRX-888-v<REV>.step`) — ME always has the current board to design the case
around, without unpacking the fabrication zip. Between releases the same STEP is
in the `release-package` CI artifact on each PR/run.

## Mechanical fit-check CI

The reusable **`.github/workflows/mechanical-build.yml`** builds a one-file
mechanical fit-check; it's called by **`mechanical-ci.yml`** (on `design`/`dev-*`
+ PRs) and by **`dev-release.yml`** (on `dev`, folded into the `v0.x` snapshot).
It:

1. exports STEP + a KiCad-native **coloured** GLB from the main board and both end
   plates (`kicad-cli`),
2. runs **`assemble_mechanical.py`** (CadQuery) to place all four parts —
   enclosure, board, front plate, rear plate — in one frame, **`assemble_glb.py`**
   to build the coloured assembly GLB (a STEP import drops colour; KiCad's
   per-board GLB keeps silk/mask/pad colours), then **`make_3d_viewer.py`**, and
3. uploads three artifacts: **`…-assembly.step`** (any CAD tool), **`…-assembly.glb`**
   (glTF), and **`…-mechanical-viewer.html`** (self-contained, offline, any browser).

Alignment is defined in `assemble_mechanical.py` — board at the 7.9 mm rail
height, width centred, length down the case; plates seat at the ends. Non-gating
during bring-up.

### Live viewer on GitHub Pages

The viewer publishes to **<https://ringof.github.io/TAPRx888/>** (the site
`index.html`), refreshed on every mechanical build — from `mechanical-ci` on
`design`/`dev-*`, and from `dev-release` on `dev` (the two share a `pages`
concurrency group so they never double-deploy). Never from a PR. **One-time
setup:** *Settings → Pages → Source: GitHub Actions*; if a deploy is rejected for a
branch, allow it under *Settings → Environments → `github-pages` → Deployment
branches*.

> A GitHub **Wiki page can't embed the viewer** — wiki HTML is sanitised (scripts
> and the `<model-viewer>` component are stripped). Link to the Pages URL.

> Board **connector** 3D models are still missing (issue #45), so the assembly
> omits those parts; everything else resolves from the vendored `3d/` mirror.

## Geometry — where it comes from, and what's still a placeholder

These are **starter boards**, not fabrication-ready. They were authored outside
KiCad, so step one is always to **open each in KiCad 10 and confirm it parses.**

**From the enclosure (solid):** the outline and mounting holes were taken from a
FreeCAD cross-section of the extrusion end (DXF, centred on 0,0):

- **Outline** — **88 × 38 mm, corner radius 4.5 mm** (the full end face).
- **Four M3 corner mounting holes** — **Ø3.4 mm at (±41, ±14.21)** from centre
  (an 82 × 28.42 mm pattern). The plate **screws on**; it is not a slide-in
  panel. (The 84.2 mm groove measured earlier is the internal **PCB** slot, not
  the plate.)

**From the main board (solid):** cutout X's are the real connector positions
mapped to plate-centred coords, `plate-X = 44 + (board-X − 138)`:

- **SMA `J1/J3/J2/J4`** (front) → −27 / −9 / +9 / +26.8 mm from centre
- **USB `J5`** (rear, X-mirrored) → −19 mm from centre (plate X = 25.04)
- **JTAG `J11` is internal** — no panel cutout.

**Connector vertical (Y) — set** from the measured **7.9 mm PCB rail height**
above the enclosure floor (the plate's **top** edge, Y=0 — verified against
`enclosure.step`). The connectors clear the bottom corner screws (those are out
at the corners).

**Cutouts — specified:**

- **SMA holes — Ø7.0 mm**, at plate **Y = 7.9** (edge-launch, board plane).
- **USB opening — 12.5 × 12.7 mm** (12 × 12.2 connector face + clearance), at
  plate **Y = 14.79** — its bottom edge is flush with the board's top surface
  (7.9 + half of the 1.57 mm board) and the connector rises 12.2 mm into the box,
  so its centre sits above the SMA plane.
- **Rear plate is X-mirrored** vs the front (the panel is viewed from outside,
  facing opposite the front); the USB opening sits at plate X = 25.04.

**Still to do before fab:**

- **Open each board in KiCad 10 to confirm it parses** (authored outside KiCad).
- **Orientation overlay** — drop each plate onto its enclosure end (or the STEP)
  and confirm the **J1 hole sits under J1** and **J5 under J5**. All X/Y match the
  board; this just blesses which face points out.

Each board carries the key parameters as a note on its `Cmts.User` layer. The
shortened enclosure (`enclosure.step`) is in place, so the outline, holes, and
cutouts can be checked against it directly.
