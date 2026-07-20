#!/usr/bin/env python3
"""Assemble the TAPRX-888 mechanical fit-check STEP.

Takes the four part STEPs -- the enclosure, the main board, and the two end
plates -- places them in a single shared coordinate frame, and writes one
multi-component STEP a reviewer can open in any CAD viewer to eyeball the fit.

This file is the *mechanical definition* of how the parts align. All the numbers
come from the board <-> enclosure work: the board sits RAIL mm above the floor,
its width centred and its length running down the case; the plates seat at the
two ends and fill the 88 x 38 opening.

Frames
------
Enclosure STEP (mechanical/enclosure.step) is the master frame:
  X = width   (centred on 0, ~ +/-44)
  Y = height  (floor = min-Y face; top = max-Y face; ~ +/-19)
  Z = length  (0 .. ~100)
Each KiCad board is exported by kicad-cli in its own frame (in-plane X/Y, the
copper stack along Z) and is rotated/translated into the enclosure frame here.

Caveats (first-run verification)
--------------------------------
* The main board's connector 3D models are still missing (issue #45), so the
  board STEP is the substrate + whatever models resolve. This is an *envelope*
  fit-check until those land.
* kicad-cli's Y-sign and the plate "floor" edge are reconciled with the flip
  flags below. Open the first CI output; if a plate's cutouts sit on the wrong
  edge, flip its *_FLIP_FLOOR flag. If the whole board is upside-down in the
  case, flip BOARD_FLIP_FLOOR.
"""
import argparse
import cadquery as cq
from cadquery import importers, Assembly, Color

# ---- mechanical definition (mm, enclosure frame) ----------------------------
RAIL = 7.9            # board mid-plane height above the enclosure floor
# Board is authored with its length along KiCad-Y and width along KiCad-X; the
# copper stack (thickness) is along KiCad-Z. Rotating +90 deg about X maps
# length -> enclosure Z and thickness -> enclosure Y.
BOARD_LEN_TO_Z_DEG = 90

# Orientation reconciliation (see caveats). Defaults are the best guess; the
# first CI artifact is the check that confirms or flips them.
BOARD_FLIP_FLOOR = True    # 180 about the length axis -- flip the board over
# First CI artifact showed the plate cutouts on the far edge from the board, so
# both plates flip about X to drop the cutouts onto the connector edge. The STEP
# carries no silkscreen, so this is purely the hole positions (X order preserved).
FRONT_FLIP_FLOOR = True
REAR_FLIP_FLOOR  = True
# The rear panel is mounted facing the opposite way (its artwork is X-mirrored),
# so it is spun 180 about the vertical (Y) axis to face outward at the USB end
# and bring its USB cutout onto the connector. The front panel faces out as-is.
REAR_FACE_FLIP_DEG = 180

COL = {
    "enclosure":      Color(0.62, 0.64, 0.66, 0.35),  # translucent aluminium
    "main-board":     Color(0.10, 0.45, 0.20, 1.00),  # PCB green
    "endplate-front": Color(0.15, 0.35, 0.70, 1.00),  # blue
    "endplate-rear":  Color(0.15, 0.35, 0.70, 1.00),
}


def load(path):
    return importers.importStep(path).val()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ("enclosure", "board", "front", "rear"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    enc = load(a.enclosure)
    eb = enc.BoundingBox()
    floor = eb.ymin
    ymid = (eb.ymin + eb.ymax) / 2.0

    # --- main board: rotate length->Z / thickness->Y, then seat in the case ---
    board = load(a.board).rotate((0, 0, 0), (1, 0, 0), BOARD_LEN_TO_Z_DEG)
    if BOARD_FLIP_FLOOR:
        board = board.rotate((0, 0, 0), (0, 0, 1), 180)
    bb = board.BoundingBox()
    board = board.translate((
        -bb.center.x,                                     # centre width on X=0
        (floor + RAIL) - bb.center.y,                     # mid-plane at rail height
        (eb.zmin + (eb.zlen - bb.zlen) / 2.0) - bb.zmin,  # centre length in case
    ))

    # --- end plates: fill the opening (centre X & Y), seat just outside an end -
    def place_plate(shape, at_z_max, face_flip_deg, floor_flip):
        if face_flip_deg:
            shape = shape.rotate((0, 0, 0), (0, 1, 0), face_flip_deg)
        if floor_flip:
            shape = shape.rotate((0, 0, 0), (1, 0, 0), 180)
        pb = shape.BoundingBox()
        dz = (eb.zmax - pb.zmin) if at_z_max else (eb.zmin - pb.zmax)
        return shape.translate((-pb.center.x, ymid - pb.center.y, dz))

    front = place_plate(load(a.front), at_z_max=True,  face_flip_deg=0,
                        floor_flip=FRONT_FLIP_FLOOR)                 # SMA end
    rear = place_plate(load(a.rear), at_z_max=False, face_flip_deg=REAR_FACE_FLIP_DEG,
                       floor_flip=REAR_FLIP_FLOOR)                   # USB end

    assy = Assembly(name="TAPRX-888-mechanical")
    for shape, name in ((enc, "enclosure"), (board, "main-board"),
                        (front, "endplate-front"), (rear, "endplate-rear")):
        assy.add(shape, name=name, color=COL[name])
    assy.save(a.out)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
