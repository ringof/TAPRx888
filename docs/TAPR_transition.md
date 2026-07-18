# TAPR Transition — working notes

Handing this work back to **`TAPR/TAPRx888`** as the canonical repo. `ringof/TAPRx888`
was a fast staging ground to get the work done and **goes fallow after handoff**.

> **Prime directive: get it right the first time.** The TAPR maintainers were about
> to *delete-and-restart* over merge/folder chaos. We do **not** experiment or debug
> live on TAPR. Everything is **perfected and fully tested in `ringof` first**, then a
> known-good state is transplanted to TAPR.

---

## 1. Operating model (the people workflow)

Roles drive everything — the git plumbing must stay invisible to the humans.

- **Paul** → pulls, edits, pushes to **`design`**, and *nothing else*. `design` is
  **unprotected** so he never fights git. Made as frictionless as possible.
- **`ci-docs`** → George's **review surface**: human-readable ERC/DRC/BOM/schematic
  PDF, published so he can eyeball them (raw URLs) without touching git or downloading
  artifacts. Generated from **`design`** activity.
- **George** → reviews `ci-docs`, says yes/no, merges **`design → dev`** (`dev`
  protected).
- **George / repo owner** → merges **`dev → main`** when production-ready (`main`
  protected). `main` spins out the production package as the **"Latest"** GitHub
  Release (the link in the repo's right-sidebar Releases widget).

### Branch model
`design` (unprotected, Paul) → `dev` (protected) → `main` (protected).
This **differs** from ringof's `feature → dev → main`; the CI triggers must be
re-pointed. `ci-docs` is a published-output branch George reads, not a work branch.

---

## 2. Versioning policy

**`main` advances to the next whole `.0` (a production board spin). `dev` does the
minor increments building toward it.** `dev`'s major just follows whatever `main`
last shipped.

| Event | Version |
|---|---|
| `dev` merge, pre-1.0 | `0.6 → 0.7 → 0.8 …` (minor++) |
| **first `dev → main`** | **`1.0`** |
| `dev` merge, post-1.0 | `1.1 → 1.2 → 1.3 …` (minor++ in the 1.x line) |
| **next `dev → main`** | **`2.0`** |
| `dev` merge, post-2.0 | `2.1 → 2.2 …` |
| **next `dev → main`** | **`3.0`** |

Mental model for hardware: **major = production spin, minor = dev iteration toward
the next spin.**

Mechanics:
- **`main` release** = `<current major + 1>.0`; first-ever → `1.0`. Every production
  release is a major by definition — **no manual major decision needed.** Published as
  a normal (non-prerelease) Release so it becomes "Latest."
- **`dev` pre-release** = minor increment within the *current major line*, where the
  line's major = the latest `main` release's major (`0` pre-1.0). First `dev` merge
  after a `main` `.0` starts at `.1` (e.g. after `1.0` → `1.1`). Published with
  `--prerelease` so it never claims "Latest."
- Keep a manual `version` override for corrections/re-publishes (idempotent clobber).

> ⚠️ This is **inverted** from what ringof currently ships (ringof `main` auto-*minors*
> with a manual major button; `dev` seeds/bumps a flat pre-release line). Both
> `prepare` blocks need reworking — see gap #1.

---

## 3. Gap analysis — fix & TEST in `ringof` before transplant

Ordered roughly by importance. `[ ]` = to do.

### [ ] 3.1 Versioning logic rework (the big one)
- Rewrite `main-release.yml` `prepare`: first → `1.0`, else → `<major+1>.0`. Drop the
  auto-minor / manual-major logic.
- Rewrite `dev-release.yml` `prepare`: minor-increment **within the current major
  line** (major = latest non-prerelease release's major, `0` if none). First dev after
  a `main .0` → `<major>.1`. Keep the pre-1.0 `0.x` behavior.
- **Testing:** the version computation is hard to test without actually cutting to
  `main`. Extract it into a standalone script (e.g. `scripts/next_version.sh LANE`)
  that both workflows call, and unit-test it against fabricated tag inputs
  (`0.6→0.7`, `→1.0`, `→1.1→1.2`, `→2.0`, `→2.1`). This also DRYs the logic across the
  two lanes.

### [ ] 3.2 CI branch-model rewire (`design → ci-docs → dev → main`)
- `dev-checks.yml`: currently triggers on `dev-*` push + PRs into `dev`/`main`.
  Re-point to trigger on **`design`** push (Paul) + PRs into `dev`/`main`.
- **`ci-docs` publish**: currently push-only on `dev-*`. Re-point to publish on
  **`design`** pushes so George always has a fresh review surface.
- `dev-release.yml` (push to `dev`) and `main-release.yml` (push to `main`): triggers
  stay, but version logic per 3.1.
- **Testing in ringof:** add a `design` branch to ringof and model the real flow —
  push to `design` → confirm `ci-docs` updates with readable ERC/DRC/BOM/PDF → merge
  `design → dev` → confirm a `dev` pre-release → merge `dev → main` → confirm the
  production release. Validate George's review path end-to-end.

### [ ] 3.3 CI image decoupling (kill the ringof dependency)
- Current image `ghcr.io/ringof/kicad-ci:10-20260704` = INTI-CMNB KiBot image +
  PyMuPDF. If ringof goes fallow, this becomes a time bomb for TAPR CI.
- **PyMuPDF is only needed for the Draftsman-like framed drawings (Phase B), which are
  NOT used in the current Phase-A pipeline** (our assembly PDF is plain `kicad-cli`).
  So the **stock public INTI-CMNB KiBot image** should cover everything we run today.
- Action: identify the exact public INTI-CMNB tag for KiCad 10, re-point all three
  workflows at it, and confirm parity (gerbers, drill, CPL, LCSC BOM, iBOM, schematic
  + assembly PDFs). Decide separately whether TAPR wants the framed drawings (→ TAPR
  would then need its own +PyMuPDF image).

### [ ] 3.4 `ci-docs` review flow — confirm it actually serves George
- Verify the published reports (raw URLs to `erc.rpt`, `drc.rpt`, `bom.csv`,
  `bom_check.txt`, schematic PDF) are genuinely reviewable at a glance. This is
  George's daily surface; if it's clumsy, the whole model suffers.

### [ ] 3.5 De-ringof-ification checklist (applied at transplant, list now)
- `.kicad_pro` text variables: `REPO`, `DESIGNER`, `LICENSE` → TAPR values.
- `github.com/ringof/…` → `github.com/TAPR/…` in `README`, `VERSION.txt`,
  `RELEASE_STRATEGY.md`, `CLAUDE.md`, `CONTRIBUTING.md`.
- Workflow container ref → the public/TAPR image (3.3).
- `usb3-fiber` provenance comments (cosmetic).

### [ ] 3.6 Known design / footprint / data issues (the *real* review work)
Not transition blockers, but this is the accuracy work that actually matters:
- **J2 SMA connector LCSC mismatch**: `C914558` vs J1/J4 `C2874826` (KiBot W004).
- **3D-model footprints** via `${TIS}` / `${KISYS3DMOD}` — STEP + renders deferred
  (issue #45).
- `${REFERENCE}` KiBot expansion error (cosmetic, non-fatal).
- `W020` resistor value-format warnings (`R-51Ω-0603` unparseable by KiBot units).
- 6 BOM rows incomplete: `L2`, `TP21` (missing LCSC); `U12/U13/U15/U17` (missing
  Value).

### [ ] 3.7 Misc
- `ENFORCE` gating is `false` (bring-up). Decide when to flip ERC/DRC to gating and
  register them as required status checks.
- `VERSION.txt` is manually maintained (currently `v0.6-dev`). Confirm we keep it
  manual vs. CI-updated.

---

## 4. Transition mechanics (only after ringof is proven & tested)

1. **Seed TAPR from ringof's known-good tree** — "mirror as a one-time reset." This is
   the clean version of the delete-and-restart the maintainers wanted. Overwrite
   TAPR's tree with ringof's flattened, de-junked, de-ringof-ified state (Paul's
   `c01bece` design is already in it; the `- Copy/` junk + `~*.lck` are already
   dropped).
2. **Stand up TAPR infra** (owner has admin):
   - Create `design`, `dev`, `main`. Set `dev` (or `main`?) default; `design`
     unprotected, `dev`/`main` protected with the right merge rules + Actions-bot
     permissions.
   - Enable Actions; workflow permissions `contents: write` for releases.
   - Point CI at the public image (3.3) — no TAPR-hosted image needed if Phase A only.
   - Populate the **wiki** with the reference-manual PDFs / RX888 docs (they were moved
     out of the repo).
   - Optional `release` Environment + required reviewer if an approval gate is wanted.
3. **Prove the full flow on TAPR** with a throwaway cycle before Paul/George rely on
   it: `design` push → `ci-docs` → `dev` pre-release → `main` production release. No
   handoff until a real package pops out the far end on TAPR.
4. **Handoff**: ringof goes fallow (archive or leave quiet). Reference-doc/README links
   point at TAPR. Recreate still-relevant issues on TAPR (they don't travel with git):
   #45 (3D models), the ERC/DRC baseline items.

---

## 5. Ownership / access
- **`ringof` work** (fix + test everything above): assistant prepares, owner reviews.
- **TAPR settings** (branches, protection, Actions, image, wiki, environments,
  permissions): repo owner (has TAPR admin). Assistant is scoped to `ringof` and
  **cannot** write to TAPR.

## 6. Open decisions
- Does TAPR want the Draftsman-like framed assembly/fab drawings (→ +PyMuPDF image),
  or is the Phase-A package enough?
- Default branch on TAPR: `dev` (matches ringof) or `design`?
- Post-cutover fate of ringof: archive vs. leave dormant.
