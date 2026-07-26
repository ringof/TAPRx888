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

## Versioning — deliberately separate from the board

A change under `mechanical/` **does not cut a board release.** The
`dev-release` / `main-release` version lanes are scoped to the **root board's**
files only, so an end-plate silkscreen tweak never bumps the board's `vX.Y`. The
end plates are simple; build their fab outputs **on demand** for now
(`kicad-cli pcb export gerbers mechanical/endplate-front/…`, or the JLCPCB
plugin). A dedicated end-plate CI lane is a possible later addition, not a
requirement.

## The board STEP is the interface

Mechanical design works from the board's exported **STEP** (board outline,
thickness, connector positions, component heights, mounting holes). The 3D models
are now resolved (all vendored in-repo, see `3d/README.md`), so `main-release`
publishes the fully-populated board STEP as a **standalone release asset**
(`TAPRX-888-v<REV>.step`) — ME always has the current board to design the case
around, without unpacking the fabrication zip. Between releases the same STEP is
in the `release-package` CI artifact on each PR/run.

## Mechanical fit-check CI

`.github/workflows/mechanical-ci.yml` builds a **one-file mechanical fit-check**
on board or `mechanical/**` changes (and on demand). It:

1. exports STEP from the **main board** and **both end plates** (`kicad-cli pcb
   export step`),
2. runs **`scripts/assemble_mechanical.py`** (CadQuery) to place all four parts —
   enclosure, board, front plate, rear plate — in one shared frame, and
3. uploads three review artifacts:
   - **`TAPRX-888-mechanical-assembly.step`** — multi-component STEP for any CAD tool,
   - **`…-assembly.glb`** — the same assembly as binary glTF (Windows 3D Viewer, VS Code, Blender, web),
   - **`…-mechanical-viewer.html`** — a **self-contained web page** (model-viewer + the GLB inlined) that spins the assembly in any browser, offline, no tools.

`scripts/assemble_mechanical.py` is the **alignment definition** — the board sits
at the 7.9 mm rail height, width centred, length down the case; the plates seat
at the ends and fill the opening. It's **non-gating** during bring-up.

### Live viewer on GitHub Pages

The `pages` job publishes the viewer to **GitHub Pages** so the wiki can link a
live URL instead of a download:

> **<https://ringof.github.io/TAPRx888/>** — refreshes on every mechanical build.

The viewer HTML becomes the site `index.html`. The job runs on push / manual
dispatch only (never from a PR — a PR must not move the live site) and is
non-gating. **One-time setup:** *Settings → Pages → Source: **GitHub Actions*** (the
workflow also asks the API to enable it via `configure-pages`, so the first run
usually turns it on by itself). If the deploy is rejected for the branch, allow it
under *Settings → Environments → `github-pages` → Deployment branches*.

> A GitHub **Wiki page cannot embed the viewer directly** — wiki HTML is
> sanitised, so `<script>` and the `<model-viewer>` web component are stripped.
> Link to the Pages URL; don't paste the HTML into a wiki page.

> Envelope-level for now: the board's connector 3D models are still missing
> (3D-models issue), so the board STEP is substrate + whatever resolves. The
> assembly script carries `*_FLIP_*` flags to reconcile orientation — the first
> CI artifact is the pass that confirms them (see the script's caveats).

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
