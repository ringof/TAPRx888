#!/usr/bin/env python3
"""Assemble the coloured mechanical GLB from KiCad's per-board GLB exports.

KiCad's own GLB export carries the silkscreen / soldermask / pad colours that a
STEP import drops -- but only one board per file. This places those coloured
GLBs (plus the grey enclosure GLB) into one scene, reusing the CadQuery
placement matrices so the result matches the STEP assembly exactly.

glTF is +Y up while the placement matrices are in the enclosure's Z-up frame, so
each matrix is conjugated by the Z-up <-> Y-up rotation before it is applied to a
(Y-up) GLB: M_glb = Rx(-90) @ M @ Rx(90).
"""
import argparse
import json

import numpy as np
import trimesh


def Rx(deg):
    return trimesh.transformations.rotation_matrix(np.radians(deg), [1, 0, 0])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--matrices", required=True)
    ap.add_argument("--enclosure", required=True)
    ap.add_argument("--board", required=True)
    ap.add_argument("--front", required=True)
    ap.add_argument("--rear", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    mats = json.load(open(a.matrices))
    zup2yup, yup2zup = Rx(-90), Rx(90)
    parts = {"enclosure": a.enclosure, "main-board": a.board,
             "endplate-front": a.front, "endplate-rear": a.rear}
    # KiCad exports GLB in METRES; the enclosure GLB (CadQuery) and the placement
    # matrices are in mm. Scale the KiCad parts by 1000 so everything is mm.
    UNIT = {"enclosure": 1.0, "main-board": 1000.0,
            "endplate-front": 1000.0, "endplate-rear": 1000.0}

    scene = trimesh.Scene()
    for name, path in parts.items():
        s = UNIT[name]
        m_glb = (zup2yup @ np.array(mats[name]) @ yup2zup) @ np.diag([s, s, s, 1.0])
        loaded = trimesh.load(path, force="scene")
        raw = loaded.bounding_box.extents
        meshes = loaded.dump()
        for i, mesh in enumerate(meshes):
            mesh.apply_transform(m_glb)
            scene.add_geometry(mesh, node_name="%s_%d" % (name, i))
        print("[glb] %-14s meshes=%2d  raw_extents=%s  placed_at=%s"
              % (name, len(meshes), np.round(raw, 3),
                 np.round(m_glb[:3, 3], 2)))
    print("[glb] combined extents=%s centroid=%s"
          % (np.round(scene.bounding_box.extents, 2),
             np.round(scene.bounding_box.centroid, 2)))
    scene.export(a.out)
    print("wrote", a.out, "-", len(scene.geometry), "geometries")


if __name__ == "__main__":
    main()
