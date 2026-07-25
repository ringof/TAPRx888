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

> Status: scaffold. Drop the enclosure STEP and the end-plate KiCad projects
> here as they're created.
