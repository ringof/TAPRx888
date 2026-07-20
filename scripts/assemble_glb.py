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

    scene = trimesh.Scene()
    for name, path in parts.items():
        m_glb = zup2yup @ np.array(mats[name]) @ yup2zup
        loaded = trimesh.load(path, force="scene")
        for i, mesh in enumerate(loaded.dump()):   # world transforms baked in
            mesh.apply_transform(m_glb)
            scene.add_geometry(mesh, node_name="%s_%d" % (name, i))
    scene.export(a.out)
    print("wrote", a.out, "-", len(scene.geometry), "geometries")


if __name__ == "__main__":
    main()
