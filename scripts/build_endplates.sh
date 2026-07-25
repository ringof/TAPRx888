#!/usr/bin/env bash
# Build the mechanical end-plate fabrication packages for a release.
#
# The end plates (mechanical/endplate-front, mechanical/endplate-rear) are
# non-functional enclosure parts fabricated as 2-layer PCBs. They are versioned
# and released independently of the board on a combined "endplates-vX.Y" lane
# (see docs/RELEASE_STRATEGY.md), so this is a separate, lighter build than
# scripts/build_release.sh -- no BOM/CPL/assembly (there are no components).
#
# Order mirrors build_release.sh: provenance (title-block rev + GIT_HASH) is
# injected into the ephemeral checkout FIRST, then the exporters generate from
# the already-stamped design. Nothing is committed back.
#
# Per plate it produces, under out/:
#   <plate>-v<EPREVISION>-gerbers.zip   gerbers + Excellon drill (fab data)
#   <plate>-v<EPREVISION>-fab.pdf       framed human-readable fab drawing
#
# Requires env: EPREVISION, GIT_HASH.
set -euo pipefail

: "${EPREVISION:?EPREVISION required}"
: "${GIT_HASH:?GIT_HASH required}"

# Absolute worksheet path so the title-block frame renders regardless of which
# plate subdirectory the .kicad_pcb lives in. The plates' page_layout_descr_file
# already points here relatively, but we pass it explicitly (as build_release.sh
# does) so the frame never depends on locally-blankable project state.
ROOT="$PWD"
WKS="$ROOT/TAPR.kicad_wks"

OUT="$ROOT/out"
mkdir -p "$OUT"

# name:dir for each plate. Keep the two in lock-step on one combined version.
PLATES=(
  "endplate-front:mechanical/endplate-front"
  "endplate-rear:mechanical/endplate-rear"
)

for entry in "${PLATES[@]}"; do
  name="${entry%%:*}"
  dir="${entry#*:}"
  pcb="$dir/$name.kicad_pcb"
  pro="$dir/$name.kicad_pro"
  stem="${name}-v${EPREVISION}"

  echo "=== Building $name (v${EPREVISION}, git ${GIT_HASH}) ==="

  # --- Inject provenance (build-time only; never committed back) --------------
  # A plate is a PCB-only project: no schematic sheets, so --sheets is empty.
  # GIT_HASH lands in the plate's own .kicad_pro text variables; rev in its PCB
  # title block. Both render in the shared TAPR worksheet frame.
  python3 scripts/inject_provenance.py \
    --revision "$EPREVISION" --git-hash "$GIT_HASH" \
    --pro "$pro" --pcb "$pcb" --sheets

  # --- Fab data: gerbers + drill (no title-block frame on fab layers) ---------
  gdir="$(mktemp -d)"
  kicad-cli pcb export gerbers "$pcb" -o "$gdir/" \
    --layers "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
  kicad-cli pcb export drill "$pcb" -o "$gdir/" \
    --format excellon --drill-origin absolute --excellon-units mm
  ( cd "$gdir" && zip -qr "$OUT/${stem}-gerbers.zip" . )
  rm -rf "$gdir"

  # --- Human-readable framed fab drawing --------------------------------------
  # Outline + holes (Edge.Cuts), copper, silk and the mechanical annotation
  # layers, with the TAPR title-block frame. GIT_HASH threaded through as the
  # board build does.
  kicad-cli pcb export pdf "$pcb" -o "$OUT/${stem}-fab.pdf" --mode-single \
    --include-border-title --drawing-sheet "$WKS" --define-var "GIT_HASH=$GIT_HASH" \
    --layers "Edge.Cuts,F.Cu,B.Cu,F.Silkscreen,User.Comments,User.Drawings"
done

echo "Built end-plate packages for v${EPREVISION} (git ${GIT_HASH}):"
find "$OUT" -type f | sort
