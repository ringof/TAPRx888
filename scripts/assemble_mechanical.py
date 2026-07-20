#!/usr/bin/env python3
"""Assemble the TAPRX-888 mechanical fit-check STEP + emit placement matrices.

Places the four parts -- enclosure, main board, and the two end plates -- in one
shared coordinate frame using CadQuery, and:
  * writes the multi-component STEP (for any CAD viewer), and
  * writes each part's 4x4 placement matrix to JSON, plus the enclosure alone as
    a GLB, so scripts/assemble_glb.py can build the *coloured* GLB from KiCad's
    own per-board GLB exports (which carry the silkscreen/soldermask/pad colours
    that a STEP import drops).

This file is the mechanical *definition* of how the parts align. See the caveats
in the git history / mechanical/README.md.

Frames: the enclosure STEP is the master frame -- X = width (centred), Y = height
(floor = min-Y), Z = length (0..~100). Each KiCad board is exported in its own
frame (in-plane X/Y, stack along Z) and rotated/translated into the enclosure
frame here.
"""
import argparse
import json

import numpy as np
import cadquery as cq
from cadquery import importers, Assembly, Color

# ---- mechanical definition (mm, enclosure frame) ----------------------------
RAIL = 7.9              # board mid-plane height above the enclosure floor
BOARD_LEN_TO_Z_DEG = 90  # rotate board length (KiCad-Y) onto enclosure Z
BOARD_END_OVER_END = True   # 180 about the width axis -- flip the board over
FRONT_FLIP_FLOOR = True     # 180 about X so the front cutouts sit at the floor
REAR_FLIP_FLOOR = True
REAR_FACE_FLIP_DEG = 180    # rear panel faces the opposite way (mirror)

COL = {
    "enclosure":      Color(0.62, 0.64, 0.66, 0.35),  # translucent aluminium
    "main-board":     Color(0.10, 0.45, 0.20, 1.00),
    "endplate-front": Color(0.15, 0.35, 0.70, 1.00),
    "endplate-rear":  Color(0.15, 0.35, 0.70, 1.00),
}


def load(path):
    return importers.importStep(path).val()


def _rot(axis, deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    if axis == "x":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def _mat(R, t):
    m = np.eye(4)
    m[:3, :3] = R
    m[:3, 3] = t
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ("enclosure", "board", "front", "rear"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--out", required=True, help="multi-component STEP")
    ap.add_argument("--matrices", required=True, help="placement matrices JSON")
    ap.add_argument("--enclosure-glb", required=True, help="enclosure-only GLB")
    a = ap.parse_args()

    enc = load(a.enclosure)
    eb = enc.BoundingBox()
    floor, ymid = eb.ymin, (eb.ymin + eb.ymax) / 2.0
    mats = {"enclosure": np.eye(4)}   # enclosure is the master (identity)

    # --- main board: length->Z, thickness->Y, end-over-end, then seat in case --
    R_board = _rot("x", BOARD_LEN_TO_Z_DEG)
    board = load(a.board).rotate((0, 0, 0), (1, 0, 0), BOARD_LEN_TO_Z_DEG)
    if BOARD_END_OVER_END:
        board = board.rotate((0, 0, 0), (1, 0, 0), 180)
        R_board = _rot("x", 180) @ R_board
    bb = board.BoundingBox()
    t_board = np.array([-bb.center.x,
                        (floor + RAIL) - bb.center.y,
                        (eb.zmin + (eb.zlen - bb.zlen) / 2.0) - bb.zmin])
    board = board.translate(tuple(t_board))
    mats["main-board"] = _mat(R_board, t_board)

    # --- end plates: fill the opening, seat just outside an end -----------------
    def place_plate(shape, at_z_max, face_flip_deg, floor_flip):
        R = np.eye(3)
        if face_flip_deg:
            shape = shape.rotate((0, 0, 0), (0, 1, 0), face_flip_deg)
            R = _rot("y", face_flip_deg) @ R
        if floor_flip:
            shape = shape.rotate((0, 0, 0), (1, 0, 0), 180)
            R = _rot("x", 180) @ R
        pb = shape.BoundingBox()
        dz = (eb.zmax - pb.zmin) if at_z_max else (eb.zmin - pb.zmax)
        t = np.array([-pb.center.x, ymid - pb.center.y, dz])
        return shape.translate((t[0], t[1], t[2])), _mat(R, t)

    front, mats["endplate-front"] = place_plate(
        load(a.front), at_z_max=True, face_flip_deg=0, floor_flip=FRONT_FLIP_FLOOR)
    rear, mats["endplate-rear"] = place_plate(
        load(a.rear), at_z_max=False, face_flip_deg=REAR_FACE_FLIP_DEG, floor_flip=REAR_FLIP_FLOOR)

    # --- STEP (for CAD) ---------------------------------------------------------
    assy = Assembly(name="TAPRX-888-mechanical")
    for shape, name in ((enc, "enclosure"), (board, "main-board"),
                        (front, "endplate-front"), (rear, "endplate-rear")):
        assy.add(shape, name=name, color=COL[name])
    assy.save(a.out)
    print("wrote", a.out)

    # --- placement matrices + enclosure GLB (for the coloured GLB assembly) -----
    with open(a.matrices, "w") as f:
        json.dump({k: v.tolist() for k, v in mats.items()}, f, indent=1)
    print("wrote", a.matrices)
    Assembly(name="enc-root").add(enc, name="enclosure",
                                  color=COL["enclosure"]).save(a.enclosure_glb, exportType="GLTF")
    print("wrote", a.enclosure_glb)


if __name__ == "__main__":
    main()
