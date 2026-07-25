#!/usr/bin/env python3
"""Validate the TAPRX-888 3D-model references.

Guards the two-tier scheme (see 3d/README.md):
  - stock models resolve via ${KICAD10_3DMODEL_DIR} (present in any KiCad
    install / the CI image) -- not checkable here, only counted;
  - custom models resolve via ${KIPRJMOD}/3d/<file> -- these live in this repo,
    so their presence IS checkable and is checked.

Always FAILS if any legacy/unresolvable reference survives the remap
(${TIS}, the :TIS: nickname, or the deprecated ${KISYS3DMOD}).

With --require-local it additionally FAILS if any BOARD-USED ${KIPRJMOD}/3d/
model file is missing. "Board-used" = referenced by a footprint in
TAPRX-888.kicad_pcb; models referenced only by an (unplaced) Library.pretty
footprint are reported but do not gate, since they never enter the board STEP.

Usage:
    python3 scripts/check_3d_models.py [--require-local] [ROOT]
"""
import re, sys, os

LEGACY = ('${TIS}', ':TIS:', '${KISYS3DMOD}')
LOCAL_PREFIX = '${KIPRJMOD}/3d/'
STOCK_PREFIX = '${KICAD10_3DMODEL_DIR}/'

def model_refs(text):
    return re.findall(r'\(model "([^"]+)"', text)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    require_local = '--require-local' in sys.argv[1:]
    root = args[0] if args else '.'

    pcb = os.path.join(root, 'TAPRX-888.kicad_pcb')
    files = [pcb]
    libdir = os.path.join(root, 'Library.pretty')
    if os.path.isdir(libdir):
        files += [os.path.join(libdir, f) for f in sorted(os.listdir(libdir))
                  if f.endswith('.kicad_mod')]

    legacy_hits, local_refs, board_used, stock = [], {}, set(), 0
    for fp in files:
        if not os.path.exists(fp):
            print(f"ERROR: missing {fp}"); return 2
        is_board = os.path.abspath(fp) == os.path.abspath(pcb)
        for m in model_refs(open(fp).read()):
            if any(tok in m for tok in LEGACY):
                legacy_hits.append((os.path.relpath(fp, root), m))
            elif m.startswith(LOCAL_PREFIX):
                rel = m[len('${KIPRJMOD}/'):]
                local_refs.setdefault(rel, os.path.exists(os.path.join(root, rel)))
                if is_board:
                    board_used.add(rel)
            elif m.startswith(STOCK_PREFIX):
                stock += 1
            else:
                legacy_hits.append((os.path.relpath(fp, root), m))  # anything unexpected

    print(f"stock (${{KICAD10_3DMODEL_DIR}}) refs : {stock}")
    print(f"local (${{KIPRJMOD}}/3d) distinct models: {len(local_refs)}")
    for rel, ok in sorted(local_refs.items()):
        tag = 'present' if ok else 'PENDING'
        scope = '' if rel in board_used else ' (library-only, unplaced)'
        print(f"   [{tag}] {rel}{scope}")

    ok = True
    if legacy_hits:
        ok = False
        print(f"\nFAIL: {len(legacy_hits)} unresolvable/legacy model reference(s):")
        for fp, m in legacy_hits[:20]:
            print(f"   {fp}: {m}")

    missing_board = sorted(r for r in board_used if not local_refs.get(r))
    missing_lib   = sorted(r for r, v in local_refs.items() if not v and r not in board_used)

    if require_local and missing_board:
        ok = False
        print(f"\nFAIL (--require-local): {len(missing_board)} board-used model file(s) missing:")
        for r in missing_board:
            print(f"   {r}")
    if missing_lib:
        print(f"\nNOTE: {len(missing_lib)} library-only model(s) missing (unplaced "
              f"footprints; do not affect the board STEP): {', '.join(missing_lib)}")

    print("\nOK" if ok else "\nFAILED")
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
