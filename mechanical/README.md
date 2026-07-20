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
- **USB `J5`** (rear) → +19 mm from centre
- **JTAG `J11` is internal** — no panel cutout.

**Connector vertical (Y) — set** from the measured **7.9 mm PCB rail height**
above the enclosure floor (the plate's **top** edge, Y=0 — verified against
`enclosure.step`), so connector centres sit at plate **Y = 7.9**. The SMA axis is
~the board plane; a **USB** connector body
sits *above* the board plane, so that opening's centre will rise once the
connector height is known (below). The connectors clear the bottom corner screws
(those are out at the corners).

**Still placeholders — verify before fab:**

- **SMA holes — Ø7.0 mm** (specified). **USB opening — 13 × 11 mm** placeholder
  (USB 3.0 Type-B) still to verify against the part; that also sets the USB
  vertical offset above the board plane.
- **Rear plate** — confirm whether X needs mirroring for the assembly's viewing
  orientation (it faces opposite the front).

Each board carries these caveats on its `Cmts.User` layer. The shortened
enclosure (`enclosure.step`) is in place, so the outline and holes can be checked
against it directly.
