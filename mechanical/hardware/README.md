# Mechanical hardware

Vendored fastener models for the mechanical fit-check (`scripts/assemble_mechanical.py`).
These are reference CAD only — for visualising the assembly, not fabrication outputs.

## `screw-M3-threadforming.step`

The enclosure end-plate corner screw: an **M3 × 0.5 thread-forming screw for
soft metal** (tri-lobular shank, Phillips pan head, ~Ø6 mm head). Source:
McMaster-Carr **94209A356** ("Thread-Forming Screws for Soft Metal").

Why this size: the box (JLCMC `K70-8838-H7`) corners are the M3 self-tap pattern
the plates were drawn from — **Ø3.4 clearance** in the plate over a **Ø2.4
self-tap channel** in the aluminium extrusion. The M3 thread passes through the
plate and forms threads in the channel. See `../README.md` and PR #61.

`assemble_mechanical.py --screw …` places 8 of these (4 corners × 2 ends), head
seated on each plate's outer face, threads pointing into the box.
