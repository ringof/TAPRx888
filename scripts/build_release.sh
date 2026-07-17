#!/usr/bin/env bash
# Build the TAPRX-888 fabrication + design package for a release, via KiBot,
# with build-time provenance injection.
#
# Order matters: provenance (title-block rev + GIT_HASH) is injected into the
# ephemeral checkout FIRST, then the exporters generate from the already-stamped
# design. KiBot never owns the revision -- it only generates. Nothing is
# committed back. See docs/RELEASE_STRATEGY.md.
#
# Preflights (ERC/DRC) are skipped here: gating already happened on the PR into
# main (dev-checks). This job just produces the package.
#
# Phase A scope: JLCPCB turnkey data (gerbers, drill, CPL, LCSC BOM), STEP,
# interactive BOM, 3D renders, and a plain framed schematic PDF (kicad-cli).
# The composited assembly / fabrication-drawing PDFs (gen_docs.sh) are Phase B.
#
# Requires env: REVISION, GIT_HASH. Produces everything under out/.
set -euo pipefail

CFG="TAPRX-888.kibot.yaml"
SCH="TAPRX-888.kicad_sch"
PCB="TAPRX-888.kicad_pcb"
WKS="TAPR.kicad_wks"
: "${REVISION:?REVISION required}"
: "${GIT_HASH:?GIT_HASH required}"

OUT="out"
mkdir -p "$OUT/docs"

# --- Inject provenance (build-time only; never committed back) ----------------
python3 scripts/inject_provenance.py --revision "$REVISION" --git-hash "$GIT_HASH"

# --- Schematic PDF (kicad-cli renders the title-block frame natively) ---------
# Pass the worksheet explicitly so the frame never depends on the project's
# page_layout_descr_file (which KiCad can blank locally). rev/date/title come
# from the title blocks stamped above; GIT_HASH is threaded through; the other
# frame variables (DESIGNER/LICENSE/REPO) come from the project text_variables.
kicad-cli sch export pdf "$SCH" -o "$OUT/docs/TAPRX-888-schematic.pdf" \
  --drawing-sheet "$WKS" \
  --define-var "GIT_HASH=$GIT_HASH"

# --- Turnkey data + iBOM + STEP via KiBot -------------------------------------
# KiBot starts its own virtual display (xvfbwrapper) for outputs that need one
# (render_3d), so we call it directly -- no xvfb-run wrapper (the image ships no
# xauth).
#
# Essential outputs -- a failure here fails the release.
kibot -c "$CFG" -e "$SCH" -b "$PCB" -d "$OUT" --skip-pre all \
  ibom step \
  JLCPCB_gerbers JLCPCB_drill JLCPCB_position JLCPCB_bom

# 3D renders are best-effort -- raytrace/3D can be flaky in headless CI and must
# not sink an otherwise-complete release.
kibot -c "$CFG" -e "$SCH" -b "$PCB" -d "$OUT" --skip-pre all \
  render_top render_bottom \
  || echo "WARN: 3D render step failed; release continues without renders."

echo "Built package for rev${REVISION} (git ${GIT_HASH}):"
find "$OUT" -type f | sort
