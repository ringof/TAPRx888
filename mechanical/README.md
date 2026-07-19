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

## Starter geometry — verify before fab

The two end-plate projects here are **starting estimates**, not
fabrication-ready. They were authored outside KiCad, so the first step is to
**open each in KiCad 10 and confirm it parses**, then reconcile against the
real enclosure:

- **Plate outline** is the nominal enclosure cross-section **88 × 38 mm**.
  Check the actual groove/slot fit against the shortened-to-100mm STEP — the
  panel that slides into the extrusion is usually a couple mm smaller.
- **Cutout X positions** are transformed from the board's real connector X's
  (SMA `J1/J3/J2/J4`, USB `J5`): plate-X = 44 + (board-X − 137). Front plate
  SMA holes land at X = 18 / 36 / 54 / 71.8; rear USB opening at X = 64.
- **Cutout vertical (Y) position** is a **placeholder at the plate centre**
  (Y = 19). The real height needs the board's seated height in the extrusion
  rail plus each connector's centre height — i.e. the 3D-models bring-over.
- **Cutout sizes** are placeholders: SMA Ø6.5 mm (1/4-32 bulkhead), USB
  13 × 11 mm (USB 3.0 Type-B). Verify against the actual parts.
- **Rear plate**: confirm whether X needs mirroring for the assembly's
  viewing orientation (it faces the opposite way from the front plate).
- **JTAG `J11` is internal** — no panel cutout.

Each board also carries these caveats as a note on the `Cmts.User` layer.
Drop the enclosure STEP (end plates removed) in as `enclosure.step` alongside.
