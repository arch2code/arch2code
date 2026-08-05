# Design Proposal: Simplify `examples/ip_test` Directory Structure

Status: DONE (2026-07-23). Collapse landed on the primary tree: `ip/ip`→`ip`,
`bridge/bridge`→`bridge`, `common/common`→`common`; `ipLeaf`→`leaf/`;
`ip_test_veh` removed. 86 `git mv` renames, user regions intact, 11 include-path
edits (grep-driven). Composed hierarchical VL green (8× "No error"). One live
`rtl.f` per project (`ip`, `bridge`, `top`=root node); the stale pre-collapse
root orphan `ip_test/rtl/{rtl.f,Makefile}` was swept (working-tree delete).
Pre-existing (NOT caused here) `test_build_manifest` failure on composed-VL
examples (`hierVlDemo` fails identically) remains for the #22 manifest work.
The directory/file refactor is committed in `196abc4` / `dd75dd8`.
Author: architecture review
Scope: `examples/ip_test` layout cleanup — remove the `ip/ip/` doubling and the
orphan directories left by the hierarchical-layout flip.

---

## 0. Locked decisions (architect, 2026-07-23) — SUPERSEDE §4.2's rename approach

The chosen approach is **collapse, not rename**. §1/§3/§5/§6 (cause, constraints,
risks, verification) still apply; §4.2's "rename to `ip/core`" is replaced by:

- **D1 + D3 — collapse the doubled node into the sub-project root for ALL three
  sub-projects.** Move each node's `yaml/` and generated segments UP one level so
  node == sub-project root, eliminating the extra subdir:
  - `ip/ip/` → `ip/` (yaml at `ip/yaml/`, segments at `ip/{base,model,rtl,fw,registrar,tb}`)
  - `bridge/bridge/` → `bridge/`
  - `common/common/` → `common/`
- **D2 — move `ipLeaf` to the root project tree** `examples/ip_test/leaf/`
  (ownership-aligned; it is `ip_test`-owned). Must happen BEFORE collapsing
  `ip/ip`, or `ip/base` etc. collide.
- **D4 — remove `examples/ip_test_veh`** (`rm -rf`; reference role discharged).
- **D5 — defer the `make db` lint;** document the convention only.
- Mechanics: `git mv` only (preserve user regions); reference paths recompute for
  BOTH moved source and moved target, so update them grep-driven (the §4.2 4-edit
  table does NOT apply to the collapse); composed hierarchical VL is the gate.

---

## 1. Why `ip/ip/` exists

### 1.1 The layout rule that produces node directories

Under `fileGeneration.layout: hierarchical`, a generated artifact is placed at:

```
<node-dir>/<functional-segment>[/module]/<file>
```

- `<functional-segment>` is the bare segment name (`base`, `model`, `rtl`, `fw`,
  `tb`, `registrar`) from the project's `dirs:` / `fileMap`
  (`expandNewModulePath`, `pysrc/processYaml.py:100-116`).
- `<node-dir>` is the **decomposition node** the object belongs to. It is NOT
  derived from block names, context names, or `includeName`. It is computed
  purely from where the authored YAML file sits on disk
  (`processSingleFile`, `pysrc/processYaml.py:5819-5826`):

```python
yamlDir = os.path.dirname(yamlFile)            # <node>/yaml
self.yamlDir = os.path.dirname(os.path.abspath(yamlDir))  # <node>
```

i.e. **the node directory is the parent of the `yaml/` directory that holds the
block's YAML file.** The node's *name* is simply whatever folder the author
created to contain `yaml/`.

### 1.2 Applying the rule to the `ip` sub-project

- The `ip` sub-project root is `examples/ip_test/ip`
  (`ip/prj/yaml/ipProject.yaml`, `dirs.root: ../..`).
- The `ip` block's YAML (`ip.yaml`, `ipTop.yaml`, `ipVariants.yaml`) lives in
  `examples/ip_test/ip/ip/yaml/`.
- Therefore the node directory = parent of that `yaml/` = `examples/ip_test/ip/ip`.

The doubling is entirely an **artifact of naming the node folder `ip` inside a
sub-project whose root folder is also named `ip`**. It is *not* inherent to the
hierarchical algorithm: the root project's own nodes (`src/`, `top/`) sit beside
`prj/` with distinct names and produce no doubling, and `common/` uses
`common/common/` and `common/cpu/` (the `common/common` node has the same
cosmetic doubling for the same reason).

### 1.3 A second, related wart: `ipLeaf` at the project root

`ipLeaf.yaml` lives at `examples/ip_test/ip/yaml/ipLeaf.yaml` — directly under
the sub-project root's own `yaml/`. Its node dir is therefore the **project root
itself** (`examples/ip_test/ip`), so `ipLeaf`'s generated segments land at
`ip/base`, `ip/model`, `ip/rtl`, `ip/fw` — mixed in beside `prj/`, `include/`,
and `verif/`. So the `ip` sub-project currently contains **two decomposition
nodes**:

| Node dir | YAML source | Blocks | Owning project |
| :--- | :--- | :--- | :--- |
| `ip/ip/` | `ip/ip/yaml/{ip,ipTop,ipVariants}.yaml` | `ip`, `ipStd*` harness | `ip` |
| `ip/` (root) | `ip/yaml/ipLeaf.yaml` | `ipLeaf` | **`ip_test`** (root) |

Note the ownership split: `ipLeaf` is referenced from the root project's
`src/yaml/src.yaml` (`../../ip/yaml/ipLeaf.yaml`), NOT from `ipProject.yaml`'s
closure. So a **root-owned** block's YAML and generated files currently live
*inside the `ip` sub-project tree*. That is a latent ownership/layout smell worth
resolving alongside the doubling (see Decision D2).

### 1.4 Identity is independent of the node folder name

Confirmed constraints that make a node rename safe:

- `includeName` (module identity / SV package name / generated file stem) is the
  **YAML file basename**, not the folder: `includeName[f] =
  os.path.splitext(os.path.basename(f))[0]` (`pysrc/processYaml.py:4104`). Moving
  `ip/ip/yaml/ip.yaml` → `ip/core/yaml/ip.yaml` keeps `includeName = ip`.
- Verilated module top names (`ip_variant0`, `ip_variant1`, `ipBridge`, …) are
  block/variant-derived, not folder-derived.
- The context key stored in `GENERATED_CODE_PARAM --context=...` is the YAML file
  path, rewritten **relative to the generated file** and recomputed every
  `make gen`; the block `.cppm/.sv/.cpp` files live *inside* the node dir, so a
  `git mv` of the node moves them together and the next `gen` rewrites the param.

---

## 2. Current tree map (source only; `.gen/`, `rundir/`, `obj_dir/` omitted)

```
examples/ip_test/
├── prj/yaml/ip_testProject.yaml     # ROOT project entry point (tests anchor here)
├── include/make/, verif/, rtl/, fw/ # root project support
├── src/{yaml,base,model,rtl,fw,registrar}      # node: src  (block: src)
├── top/{yaml,base,model,rtl,fw,registrar,tb}   # node: top  (block: ip_top, apbDecode)
│
├── ip/                              # ── 'ip' SUB-PROJECT root ──
│   ├── prj/yaml/ipProject.yaml
│   ├── include/make/, verif/{vl_wrap,blocks(EMPTY)}
│   ├── yaml/ipLeaf.yaml             # node = ip ROOT (ipLeaf, ip_test-owned)
│   ├── base|model|rtl|fw/           #   ← ipLeaf segments at project root (wart)
│   └── ip/                          # node: ip  ← DOUBLED NAME (main wart)
│       ├── yaml/{ip,ipTop,ipVariants}.yaml
│       └── base|model|rtl|fw|registrar|tb/
│
├── bridge/                          # ── 'ipBridge' SUB-PROJECT root ──
│   ├── prj/yaml/ipBridgeProject.yaml
│   ├── ip -> ../ip                  # vendored symlink (provider)
│   ├── common -> ../common          # vendored symlink (provider)
│   └── bridge/                      # node: bridge  ← same cosmetic doubling
│       ├── yaml/{ipBridge,bridgeStdTop}.yaml
│       └── base|model|rtl|fw|registrar|tb/
│
├── common/                          # ── 'common' SUB-PROJECT root ──
│   ├── prj/yaml/commonProject.yaml
│   ├── common/{yaml,fw,model,rtl}   # node: common ← same cosmetic doubling
│   └── cpu/{yaml,base,model}        # node: cpu
│
└── arch/                            # ORPHAN — entirely empty (flip leftover)
    └── yaml/bridge/                 # ORPHAN — empty
```

### 2.1 Over-nesting / orphan / redundant inventory

| Item | Path | Classification |
| :--- | :--- | :--- |
| Doubled node (primary) | `ip/ip/` | rename target |
| Doubled node (cosmetic) | `bridge/bridge/`, `common/common/` | same pattern; optional |
| Root-owned block inside sub-project | `ip/yaml/ipLeaf.yaml` + `ip/{base,model,rtl,fw}` | ownership/layout smell |
| Empty orphan | `examples/ip_test/arch/` (incl. `arch/yaml`, `arch/yaml/bridge`) | delete — no references |
| Empty orphan | `examples/ip_test/ip/verif/blocks/` | delete (empty) |

`verif/blocks/` at the root and `bridge/verif/`, `ip/verif/vl_wrap` etc. carry
Makefiles / are live — NOT orphans.

---

## 3. Ownership / identity constraints (what must NOT change)

1. **Project-file anchor.** Unit tests and the make harness reference only the
   project entry points, never internal node paths:
   - `unittest/test_addrctl_ip_test_view.py:43` and
     `unittest/test_boundary_signals.py:28` build from
     `examples/ip_test/prj/yaml/ip_testProject.yaml`.
   - `examples/ip_test/include/make/shared.mk:22`
     `A2C_PRJ_YAML = .../prj/yaml/ip_testProject.yaml`.
   - The child project files `ip/prj/yaml/ipProject.yaml`,
     `bridge/prj/yaml/ipBridgeProject.yaml`, `common/prj/yaml/commonProject.yaml`
     are referenced by path from parents.
   → Keep all `prj/yaml/*Project.yaml` file paths unchanged. An internal node
   rename does not touch them.
2. **YAML file basenames = module identity.** Do not rename `ip.yaml`,
   `ipTop.yaml`, `ipVariants.yaml`, etc. Rename only the *folder*.
3. **Reference-closure ownership** (`CONTEXTOWNINGPROJECT`) resolves by
   `projectFiles`/`include` edges + `projectName`, not by folder name. Safe under
   a node rename provided every reference edge is updated (Section 4.2).
4. **Vendored symlinks** `bridge/ip -> ../ip` and `bridge/common -> ../common`
   point at sub-project *roots*, not at inner nodes, so an inner-node rename is
   transparent to them. BUT the bridge YAML also reaches `ip`'s node through the
   **real tree** (not the symlink): `bridge/bridge/yaml/ipBridge.yaml:39` and
   `bridge/bridge/yaml/bridgeStdTop.yaml:17` both include
   `../../../ip/ip/yaml/ipVariants.yaml`. Those literal paths must be updated.
5. **Composed multi-node VL build** depends on identity-derived module tops
   (`ip_variant0/1`, `ipBridge`, `apbDecode`, …), unaffected by a folder rename;
   must be re-verified green (Section 6).
6. **Parallel vehicle copy** `examples/ip_test_veh/` mirrors this structure. It
   is a separate example — decide explicitly whether to mirror the cleanup
   (Decision D4).

---

## 4. Proposed target & migration approach

### 4.1 No generator change is required

Because the node directory is purely "parent of the `yaml/` dir", de-doubling is
a **pure file-move + YAML-reference-update** migration. There is no layout-rule
defect to fix. A generator-level auto-collapse (Option 4 below) is possible but
**not recommended** — it would add hidden magic to every project's paths for a
cosmetic naming choice.

### 4.2 Recommended target: rename the inner node `ip/ip` → `ip/core`

Rename the doubled node folder to a distinct name (recommended `core`; `ipCore`
also fine). Result:

```
examples/ip_test/ip/
├── prj/yaml/ipProject.yaml
├── include/, verif/
├── core/                       # was ip/ip  — the 'ip' block node
│   ├── yaml/{ip,ipTop,ipVariants}.yaml
│   └── base|model|rtl|fw|registrar|tb/
└── leaf/                       # (Decision D2) was ip/yaml + ip/{base,model,...}
    ├── yaml/ipLeaf.yaml
    └── base|model|rtl|fw/
```

**Exact reference edits (4 files):**

| File:line | From | To |
| :--- | :--- | :--- |
| `ip/prj/yaml/ipProject.yaml:12` | `../../ip/yaml/ipTop.yaml` | `../../core/yaml/ipTop.yaml` |
| `top/yaml/ip_top.yaml:28` | `../../ip/ip/yaml/ipVariants.yaml` | `../../ip/core/yaml/ipVariants.yaml` |
| `bridge/bridge/yaml/ipBridge.yaml:39` | `../../../ip/ip/yaml/ipVariants.yaml` | `../../../ip/core/yaml/ipVariants.yaml` |
| `bridge/bridge/yaml/bridgeStdTop.yaml:17` | `../../../ip/ip/yaml/ipVariants.yaml` | `../../../ip/core/yaml/ipVariants.yaml` |

Same-directory includes inside the node (`ipTop.yaml`→`ipVariants.yaml`→`ip.yaml`)
are relative and need no change.

### 4.3 Decisions the architect must make

- **D1 — Inner-node name.** `core` (recommended, generic/reusable) vs `ipCore`
  vs leaving it. Trade-off: `core` reads cleanly as "the IP core node"; `ipCore`
  is more explicit but re-introduces the `ip` prefix.
- **D2 — Where `ipLeaf` lives.** Three shapes:
  - (a) *Keep in `ip` sub-project, own node* `ip/leaf/` — clears the
    files-at-project-root wart, minimal reference change (`src.yaml:25`
    `../../ip/yaml/ipLeaf.yaml` → `../../ip/leaf/yaml/ipLeaf.yaml`).
  - (b) *Move to the root project tree* `examples/ip_test/leaf/` — ownership-aligned
    (ipLeaf is `ip_test`-owned), removes root-owned files from the sub-project
    entirely; larger move, `src.yaml` include becomes `../../leaf/yaml/ipLeaf.yaml`.
    **Recommended** if the intent is a clean sub-project boundary.
  - (c) *Leave as-is* — accept `ip/{base,model,...}` at the project root.
- **D3 — Cosmetic doubling in siblings.** Apply the same rename to
  `bridge/bridge` → `bridge/<name>` and `common/common` → `common/<name>` for
  consistency, or scope this change to `ip` only. Recommendation: do `ip` now
  (the flagged wart); do `bridge`/`common` in the same pass only if the architect
  wants uniformity, since each adds its own reference-edit set.
- **D4 — `ip_test_veh` mirror.** Apply the same cleanup to the vehicle copy, or
  leave it and note the divergence.
- **D5 — Convention capture.** Adopt a documented convention: *"a decomposition
  node folder must not share the name of its sub-project root folder."* Optionally
  add a `make db` advisory (non-fatal) when `node == projectRoot` basename. This
  is the only place a (small, optional) generator change would be justified, and
  only as a lint, not a path rewrite.

### 4.4 Orphan removal (independent of the rename)

- `git rm -r examples/ip_test/arch` (entire empty tree; zero references confirmed
  by grep across `*.yaml`, `*.mk`, `Makefile`).
- Remove empty `examples/ip_test/ip/verif/blocks/` (empty; the live block-verif
  dir is `verif/blocks/` at the root, which has a `Makefile`).

---

## 5. Risks & ripple analysis

| Change | Ripples into | Risk / mitigation |
| :--- | :--- | :--- |
| Rename node folder | `_context` key strings; `GENERATED_CODE_PARAM --context` in every file in the node | LOW — recomputed at `make db`, rewritten at `make gen`. **Use `git mv`, never delete+regenerate**, or user regions in `ipStd*` `.cpp/.h`, `ip.cppm`, `ipRegistrar.cppm` are lost (in-place generator will not recreate deleted files). |
| Rename node folder | module identity / SV package / file stems | NONE — identity is YAML basename, not folder. |
| Update 4 reference paths | ownership closure, cross-project resolution, composed build | MEDIUM if any edge missed → duplicate/unresolved context. Mitigate with the grep in Phase 5. |
| `ipLeaf` relocation (D2b) | root project `src.yaml` include; ipLeaf generated segments move | LOW-MED — one include edit + `git mv`; re-verify root build. |
| Delete `arch/`, `ip/verif/blocks` | none (no references) | NONE. |
| Vendored symlinks | bridge provider resolution | NONE for inner-node rename (symlink targets sub-project root); the *real-tree* bridge includes are covered by the 4-file edit. |
| Unit tests / harness | `test_addrctl_ip_test_view`, `test_boundary_signals`, make | NONE — anchored at `prj/yaml/*Project.yaml`. |
| Sibling doubling (D3) | bridge/common reference edits | Scales risk linearly per sub-project; keep each in its own commit. |

---

## 6. Phased implementation checklist

**Phase 0 — Baseline.** Record a clean composed run as the reference:
`cd examples/ip_test && make -j clean && make -j gen && make -j run && make -j run-vl`
(hierarchical composed VL green). Note the passing artifacts.

**Phase 1 — Orphan sweep.** `git rm -r examples/ip_test/arch`; remove empty
`ip/verif/blocks`. `make -j gen` — expect no diff in generated output.

**Phase 2 — Rename `ip/ip` → `ip/core` (D1).**
`git mv examples/ip_test/ip/ip examples/ip_test/ip/core` (moves YAML + all
generated segment files together, preserving user regions).

**Phase 3 — Update the 4 reference paths** exactly as in the table in §4.2.

**Phase 4 — (Optional, D2) relocate `ipLeaf`** into its own node
(`ip/leaf/` or `examples/ip_test/leaf/`); `git mv` the yaml + segment dirs and
update `src/yaml/src.yaml:25`.

**Phase 5 — Guard grep.** Confirm no stale references remain:
`grep -rn "ip/ip/\|/ip/yaml/ipTop\|/ip/yaml/ipVariants" examples/ip_test --include=*.yaml --include=*.mk --include=Makefile` → must be empty (ignoring `.gen/`, `rundir/`).

**Phase 6 — Re-verify (composed).**
`make -j clean && make -j gen && make -j run && make -j run-vl` in
`examples/ip_test` → composed hierarchical VL must be green, matching the
Phase-0 baseline. Confirm the `ip/core/` (and `ip/leaf/`) segments regenerated
and user regions are intact.

**Phase 7 — Re-verify (other examples unaffected).** Run the base (and pro)
example sweep — at minimum `apbDecode`, `axi4sDemo`, and any example touching the
shared layout code — to confirm the node-name convention change / lint (if D5
adopted) leaves untouched projects byte-identical.

**Phase 8 — Siblings & vehicle (D3/D4), convention doc (D5)** as separately
scoped commits, each with its own Phase 5/6 guard.

---

## 7. Recommendation summary

- De-doubling needs **no generator change** — it is a file-move + 4-line YAML
  reference update. Do it via `git mv` to preserve user regions.
- **Recommended shape:** rename `ip/ip` → `ip/core` (D1) and relocate `ipLeaf`
  to its own node aligned with its owner (D2b → `examples/ip_test/leaf/`, or D2a
  → `ip/leaf/` for a smaller move), plus delete the `arch/` and `ip/verif/blocks`
  orphans.
- **Defer to architect:** node name (D1), ipLeaf destination (D2), whether to
  also de-double `bridge/bridge` and `common/common` (D3), the `ip_test_veh`
  mirror (D4), and codifying the "node name ≠ sub-project root name" convention
  as a `make db` lint (D5).
- Re-verify at every phase with the composed hierarchical VL run as the gate.
