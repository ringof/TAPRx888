#!/usr/bin/env python3
"""Assemble the TAPRX-888 mechanical fit-check STEP + emit placement matrices.

Places the four parts -- enclosure, main board, and the two end plates -- in one
shared coordinate frame using CadQuery (plus, optionally, the 8 M3 corner
screws), and:
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
    "screw":          Color(0.80, 0.80, 0.83, 1.00),  # zinc-plated steel
}

# Enclosure corner mounting holes, in the enclosure (master) frame [mm]. The M3
# pattern was taken from the box end profile: Ø3.4 clearance in the plates over a
# Ø2.4 self-tap channel in the box, at (+/-41, +/-14.21), at BOTH ends. An M3
# thread-forming screw ("for soft metal") passes through the plate and taps the
# channel. Source: mechanical/README.md + enclosure.step (verified). 8 holes =
# 4 corners x 2 ends.
HOLE_XY = [(sx * 41.0, sy * 14.21) for sx in (1, -1) for sy in (1, -1)]


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


def place_screws(path, eb, t_front, t_rear):
    """Place 8 M3 thread-forming screws in the enclosure corner holes.

    Returns (shapes, mats): a list of (shape, name) and a name->4x4 dict. The
    screw axis is the enclosure length (Z); each screw's head seats on the outer
    face of its end plate and the threads point inward into the box channel.
    """
    import math

    def rad(v):
        return math.hypot(v[0], v[1])

    def verts(shape):
        return [v.toTuple() for v in shape.Vertices()]

    s0 = load(path)                                  # screw long axis is Z
    sb = s0.BoundingBox()
    vv = verts(s0)
    zc = (sb.zmin + sb.zmax) / 2.0
    r_hi = max((rad(v) for v in vv if v[2] >= zc), default=0.0)
    r_lo = max((rad(v) for v in vv if v[2] < zc), default=0.0)
    if r_hi < r_lo:                                  # head sits at -Z -> flip up
        s0 = s0.rotate((0, 0, 0), (1, 0, 0), 180)
        sb = s0.BoundingBox()
    base = s0.translate((0, 0, -sb.zmin))            # tip at origin, head toward +Z

    # Head-bearing height above the tip = lowest vertex of the (wider) head.
    vb = verts(base)
    ztop = base.BoundingBox().zmax
    thread_r = max((rad(v) for v in vb if v[2] < 0.6 * ztop), default=1.75)
    head_z = [v[2] for v in vb if rad(v) >= 1.4 * thread_r]
    Hb = min(head_z) if head_z else 0.7 * ztop       # tip -> head-bearing distance

    shapes, mats = [], {}
    # +Z end: head already points +Z (outward), no flip. -Z end: flip 180 about X.
    ends = (("front", eb.zmax + t_front, False),
            ("rear",  eb.zmin - t_rear,  True))
    for end, p_out, flip in ends:
        for i, (hx, hy) in enumerate(HOLE_XY, start=1):
            shp, R = base, np.eye(3)
            if flip:
                shp = shp.rotate((0, 0, 0), (1, 0, 0), 180)
                R = _rot("x", 180)
                tz = p_out + Hb                       # head-bearing (-Hb) -> p_out
            else:
                tz = p_out - Hb                       # head-bearing (+Hb) -> p_out
            shp = shp.translate((hx, hy, tz))
            name = "screw-%s-%d" % (end, i)
            shapes.append((shp, name))
            mats[name] = _mat(R, np.array([float(hx), float(hy), tz]))
    return shapes, mats


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ("enclosure", "board", "front", "rear"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--board-bare", required=True,
                    help="component-free board datum STEP (kicad-cli --board-only): "
                         "its bbox is the substrate mid-plane + Edge.Cuts outline, "
                         "so the board seat never moves when parts change")
    ap.add_argument("--out", required=True, help="multi-component STEP")
    ap.add_argument("--matrices", required=True, help="placement matrices JSON")
    ap.add_argument("--enclosure-glb", required=True, help="enclosure-only GLB")
    ap.add_argument("--screw", default=None,
                    help="M3 thread-forming screw STEP; if given, 8 are placed "
                         "in the enclosure corner holes (and baked into the "
                         "enclosure GLB so they appear in the viewer too)")
    a = ap.parse_args()

    enc = load(a.enclosure)
    eb = enc.BoundingBox()
    floor, ymid = eb.ymin, (eb.ymin + eb.ymax) / 2.0
    mats = {"enclosure": np.eye(4)}   # enclosure is the master (identity)

    # --- main board: length->Z, thickness->Y, end-over-end, then seat in case --
    # Seat off the component-free datum (--board-only), NOT the populated board:
    # a bounding box that includes the 3D component models drifts every time a
    # part changes height. The datum's bbox is the bare PCB, so its center is the
    # substrate mid-plane (vertical) and the Edge.Cuts outline center (lateral).
    # The datum shares the board's origin, so the transform we derive from it
    # applies verbatim to the populated board.
    def orient_board(shape):
        shape = shape.rotate((0, 0, 0), (1, 0, 0), BOARD_LEN_TO_Z_DEG)
        if BOARD_END_OVER_END:
            shape = shape.rotate((0, 0, 0), (1, 0, 0), 180)
        return shape

    R_board = _rot("x", BOARD_LEN_TO_Z_DEG)
    if BOARD_END_OVER_END:
        R_board = _rot("x", 180) @ R_board
    bb = orient_board(load(a.board_bare)).BoundingBox()   # bare PCB datum
    t_board = np.array([-bb.center.x,
                        (floor + RAIL) - bb.center.y,
                        (eb.zmin + (eb.zlen - bb.zlen) / 2.0) - bb.zmin])
    board = orient_board(load(a.board)).translate(tuple(t_board))  # populated
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

    # --- corner screws: seat head on each plate's outer face, thread into box ----
    screws = []
    if a.screw:
        screws, screw_mats = place_screws(
            a.screw, eb, t_front=front.BoundingBox().zlen, t_rear=rear.BoundingBox().zlen)
        mats.update(screw_mats)
        print("placed %d screws" % len(screws))

    # --- STEP (for CAD) ---------------------------------------------------------
    assy = Assembly(name="TAPRX-888-mechanical")
    for shape, name in ((enc, "enclosure"), (board, "main-board"),
                        (front, "endplate-front"), (rear, "endplate-rear")):
        assy.add(shape, name=name, color=COL[name])
    for shape, name in screws:
        assy.add(shape, name=name, color=COL["screw"])
    assy.save(a.out)
    print("wrote", a.out)

    # --- placement matrices + enclosure GLB (for the coloured GLB assembly) -----
    with open(a.matrices, "w") as f:
        json.dump({k: v.tolist() for k, v in mats.items()}, f, indent=1)
    print("wrote", a.matrices)
    # Bake the placed screws into the enclosure GLB: they live in the enclosure
    # (identity) frame, so assemble_glb.py -- which applies mats["enclosure"] to
    # this file -- carries them into the coloured viewer already seated.
    enc_root = Assembly(name="enc-root").add(enc, name="enclosure", color=COL["enclosure"])
    for shape, name in screws:
        enc_root.add(shape, name=name, color=COL["screw"])
    enc_root.save(a.enclosure_glb, exportType="GLTF")
    print("wrote", a.enclosure_glb)


if __name__ == "__main__":
    main()
