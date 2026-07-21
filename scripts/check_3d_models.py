#!/usr/bin/env python3
"""Validate the TAPRX-888 3D-model references.

Guards the two-tier scheme (see 3d/README.md):
  - stock models resolve via ${KICAD10_3DMODEL_DIR} (present in any KiCad
    install / the CI image) -- not checkable here, only counted;
  - custom models resolve via ${KIPRJMOD}/3d/<file> -- these live in this repo,
    so their presence IS checkable and is checked.

Always FAILS if any legacy/unresolvable reference survives the remap
(${TIS}, the :TIS: nickname, or the deprecated ${KISYS3DMOD}).

With --require-local it additionally FAILS if any ${KIPRJMOD}/3d/ model file is
missing -- flip this on in CI once every custom model has been vendored and you
re-enable the STEP / render outputs.

Usage:
    python3 scripts/check_3d_models.py [--require-local] [ROOT]
"""
import re, sys, os

LEGACY = ('${TIS}', ':TIS:', '${KISYS3DMOD}')

def model_refs(text):
    return re.findall(r'\(model "([^"]+)"', text)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    require_local = '--require-local' in sys.argv[1:]
    root = args[0] if args else '.'

    files = [os.path.join(root, 'TAPRX-888.kicad_pcb')]
    libdir = os.path.join(root, 'Library.pretty')
    if os.path.isdir(libdir):
        files += [os.path.join(libdir, f) for f in sorted(os.listdir(libdir))
                  if f.endswith('.kicad_mod')]

    legacy_hits, local_refs, stock = [], {}, 0
    for fp in files:
        if not os.path.exists(fp):
            print(f"ERROR: missing {fp}"); return 2
        for m in model_refs(open(fp).read()):
            if any(tok in m for tok in LEGACY):
                legacy_hits.append((os.path.relpath(fp, root), m))
            elif m.startswith('${KIPRJMOD}/3d/'):
                rel = m[len('${KIPRJMOD}/'):]
                local_refs.setdefault(rel, os.path.exists(os.path.join(root, rel)))
            elif m.startswith('${KICAD10_3DMODEL_DIR}/'):
                stock += 1
            else:
                legacy_hits.append((os.path.relpath(fp, root), m))  # anything unexpected

    print(f"stock (${{KICAD10_3DMODEL_DIR}}) refs : {stock}")
    print(f"local (${{KIPRJMOD}}/3d) distinct models: {len(local_refs)}")
    present = sum(1 for v in local_refs.values() if v)
    for rel, ok in sorted(local_refs.items()):
        print(f"   [{'present' if ok else 'PENDING'}] {rel}")

    ok = True
    if legacy_hits:
        ok = False
        print(f"\nFAIL: {len(legacy_hits)} unresolvable/legacy model reference(s):")
        for fp, m in legacy_hits[:20]:
            print(f"   {fp}: {m}")
    missing = [r for r, v in local_refs.items() if not v]
    if require_local and missing:
        ok = False
        print(f"\nFAIL (--require-local): {len(missing)} custom model file(s) missing:")
        for r in missing:
            print(f"   {r}")
    elif missing:
        print(f"\nNOTE: {len(missing)} custom model(s) still pending "
              f"(expected until vendored; see 3d/README.md).")

    print("\nOK" if ok else "\nFAILED")
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
