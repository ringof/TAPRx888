# Release Strategy

How TAPRX-888 versions the design, builds fabrication packages, and publishes
releases. Implemented by `.github/workflows/main-release.yml` (and
`dev-checks.yml` for pre-merge validation).

## Branches & CI

Two-tier flow: **feature → `dev` → `main`**.

- **`dev-*`** feature branches are where work happens. They merge (squash) into
  **`dev`**, the permanent integration branch (and default branch).
- **`dev`** collects vetted work. When a release is wanted, `dev` merges (squash)
  into **`main`**.
- **`main`** is the release branch. A merge here builds and (if the design
  changed) publishes a revision.
- Both `dev` and `main` are protected (PR required); `main` is the stricter
  release gate.

CI:

- **`dev-checks`** runs on `dev-*` pushes and on **PRs into `dev` and `main`**:
  ERC, DRC, BOM completeness, plus schematic PDF and gerbers/drill as artifacts.
- **`main-release`** runs on every merge to `main` (and can be dispatched
  manually) and is responsible for versions and published packages.

## Versioning

TAPRX-888 uses a **`MAJOR.MINOR`** scheme, distinct from the pre-release `0.x`
line:

- **`0.x`** — pre-release / bring-up, lives on the **dev lane**. Published only
  as GitHub **pre-releases** (or plain tags); `main-release` ignores them.
- **`1.0`** — the first `main` release.
- **`1.x`** — every subsequent `main` release **auto-increments the minor**
  (`v1.3 → v1.4`). The minor **never rolls over**: `v1.9 → v1.10 → v1.11 …`.
- **`MAJOR` bumps (`2.0`, `3.0`, …)** are **not automated** — there is no rule a
  script can apply to decide "this is a new major." A maintainer forces it with a
  manual override (below). After `v2.0` is cut, auto-increment resumes at `v2.1`.

**GitHub Releases are the source of truth.** The next version is computed by
reading the latest non-prerelease release tag and bumping the minor; no version
number is stored in the design files. Tags are `v<MAJOR>.<MINOR>`; the release
title matches the tag.

## When is a new revision cut?

`main-release` publishes a **new** revision **only when a design file changed
since the last release**. Docs/CI/script-only merges are a **no-op** — they run
the workflow, determine nothing changed, and stop without building or publishing.

**Design files** (a change to any of these triggers an uprev):

- `*.kicad_sch`, `*.kicad_pcb`, `*.kicad_pro`, `*.kicad_dru`, `*.kicad_sym`
- `Library.pretty/**`, `fp-lib-table`, `sym-lib-table`

**Not design files** (never trigger an uprev): `README.md`, `docs/**`,
`.github/**`, `scripts/**`, and `*.kicad_prl` (editor/UI state).

The comparison is made against **the last release's commit**, not just the
merge's own diff — so a design edit that landed in an earlier (unpublished)
commit is still caught, and a later docs-only merge cannot mask it.

## Manual override — how a maintainer operates it

The workflow listens to **both** an automatic trigger (`push` to `main`) and a
manual one (`workflow_dispatch`). The manual path is driven entirely by inputs —
no YAML editing.

**GitHub web UI:**

1. Repo → **Actions** → **main-release** (left sidebar).
2. **Run workflow ▾** (top-right).
3. Fill the form:
   - **Use workflow from** — for a real release pick **`main`**.
   - **version** — e.g. `2.0` to force a version; **blank** = automatic minor bump.
   - **dry_run** — tick to build + upload artifacts but publish nothing.
4. **Run workflow**.

**gh CLI:**

```sh
gh workflow run main-release.yml --ref main -f version=2.0       # force a major
gh workflow run main-release.yml --ref main -f dry_run=true      # validate only
gh workflow run main-release.yml --ref main -f version=2.0 -f dry_run=true
```

`version` sets the published version and skips auto-detection. Re-running with an
existing version is **idempotent**: the job refreshes that release's assets
(`gh release upload --clobber`) instead of failing — so it doubles as the
"re-publish / fix a release" button.

| Goal | Inputs |
|---|---|
| Cut major **2.0** | `version: 2.0` (auto resumes at 2.1) |
| Deliberately cut **1.0** | `version: 1.0` (else the first `main` merge does it) |
| Re-publish/fix **v1.4** | `version: 1.4` |
| Validate the pipeline | `dry_run: true` |

> The **Run workflow** button only appears once `main-release.yml` is on the
> **default branch** (`dev`). Dispatching requires write/Actions permission.
> Until then (and any time), the **PR preview build** below validates the
> pipeline from the pull request itself.

### Dry run (build without publishing)

`dry_run: true` builds the full turnkey package and uploads it as **run
artifacts** (`release-package`) **without** publishing a release. It forces a
build even when no design file changed, so the pipeline (e.g. a KiBot config
change) can be validated before you commit to a real release. Provenance is
still injected, so the artifacts carry the version they *would* be published
under.

### PR preview build (no button needed)

Every **pull request** into `dev` or `main` that touches the design or the
release pipeline runs `main-release` in **forced dry-run** automatically. The
full package is built and attached to the run as the `release-package`
artifact — download it straight from the PR's **Checks** tab to inspect exactly
what a release would contain, before merging. The `release` job is gated on
`publish==true` (never set for PR events), so a PR can never publish. This also
sidesteps the "Run workflow button only exists on the default branch" limitation
during initial bring-up: you can validate the pipeline from the PR itself.

### Optional approval gate

To require a human "Approve" before **every** publish (automatic or manual),
create a GitHub **Environment** named `release` with a required reviewer and
uncomment `environment: release` on the `release` job. Build and package still
run automatically; only the `gh release create` waits behind the approver.

## Provenance (`${REVISION}` and `${GIT_HASH}`)

Both are **injected at build time** (`scripts/inject_provenance.py`) into the
design and rendered into the schematic/PCB **title block** and the **bottom
silkscreen**. Nothing is committed back to the design files — the placeholders
committed in the design (`DEV` / `dev`) only apply to local opens.

- `${REVISION}` — the version being published, stamped into the `rev` field of
  **every** schematic sheet (root + `Front_End` + `refclk`) and the board, so no
  sub-sheet page renders a stale `DEV`.
- `${GIT_HASH}` — **the last commit that touched a design file**, not `HEAD`.
  Written to the `GIT_HASH` project text variable.

Stamping the *design* commit (rather than the build's `HEAD`) keeps the mark
truthful and stable: a docs-only commit never changes it, and the same physical
design never ends up stamped with two different hashes.

## Release assets

Each release attaches **stable-named** assets (no rev/hash in the filename), so
`…/releases/latest/download/<name>` links stay valid across revisions:

| Asset | Contents |
|---|---|
| `TAPRX-888-schematic.pdf` | Schematic (direct download, no unzip) |
| `TAPRX-888-assembly.pdf` | Assembly drawing — top + bottom placement (F/B.Fab + silk + edge), framed |
| `TAPRX-888-gerbers.zip` | Gerbers + drill (JLCPCB-ready) |
| `TAPRX-888-fabrication.zip` | Full package: gerbers, drill, LCSC BOM, CPL, interactive BOM, schematic + assembly PDFs |

The version and git hash live inside the files and in the release title/tag,
not in the filenames.

> **Scope notes (Phase A):**
> - A **basic** assembly drawing (top/bottom placement, framed) is included. The
>   fully composited, board-normalized **assembly** and multipage
>   **fabrication-drawing** PDFs (`scripts/gen_docs.sh` in usb3-fiber) are a
>   planned Phase B follow-up.
> - **STEP (3D model) and 3D renders** are not yet in the package. The
>   footprints reference custom 3D models via `${TIS}`/`${KISYS3DMOD}`, which
>   aren't in the CI image, so KiBot can't resolve them. Restoring them needs
>   that model library provisioned in `ghcr.io/ringof/kicad-ci` (or the 3D paths
>   remapped to KiCad's standard packages). The KiBot `step`/`render_*` outputs
>   remain defined for then.

## Edge cases

- **First release:** no prior non-prerelease → `v1.0`.
- **`v0.x` pre-releases:** excluded from version detection (marked prerelease),
  so they never cause `main` to bump `0.5 → 0.6` instead of cutting `1.0`.
- **Doc-only merge after a design change is already released:** no-op, as
  intended — the released design is unchanged.
