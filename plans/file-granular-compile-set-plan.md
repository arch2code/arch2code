# Plan: file-granular C++ compile set and instantiated-variant Verilator tops

Status: proposal, 2026-09-18. Supersedes the `A2C_CPP_EXCLUDE_FILES` interim
(base, uncommitted, fix 3 of the root VL_DUT unblock; hardened the same day to
exclude every foreign-owned `blockVlRegistrar` TU). Keeps fix 1 (the
`calcRegistrarPairs` ownership guard: pair-specific registrations are skipped
when the pair owner is not the owner of the build's top block) and fix 2
(`__ALL.a` archive merge in a2c-vl-wrap.mk), which are independent of this plan.

## 1. Problem

The manifest (`.gen/build.mk`, written by `config/createBuildManifest.py`) is
file-granular for every input except plain `.cpp` sources. Modules
(`A2C_CPP_MODULE_FILES`, 219 files in the root), SV modules, wrapper tops and
gen targets are listed per file. Plain `.cpp` sources are listed per directory
(`A2C_SC_SRC_DIRS`, 47 directories in the root) and `a2c-systemc.mk` expands
each with `$(wildcard $(dir)/*.cpp)`.

For a composed root that reuses IP directories wholesale this compiles every
generated TU in those directories whether or not the root's contract names it.
Two consequences observed in the root build on 2026-09-18:

- `debayer/registrar/interpolateVlRegistrar.cpp` (the debayer -> interpolate
  pair registrar) is swept in. The root's pair for it has no Verilated
  registrations after fix 1, so the `Vp7_..._default_hdl_sv_wrapper.h` it
  includes is never generated. Interim fix 3 subtracts nine such TUs after the
  wildcard.
- `debayer/registrar/debayerVlRegistrar.cpp` (the debayer_tb -> debayer pair
  registrar) is also swept in. The root has *no row at all* for it, because
  `calcRegistrarPairs` only walks reachable instances and debayer_tb is not
  reachable from isp_top. It compiles only because block-mode `vlSvWrap` rows
  record a top for every standalone label of every `hasVl` block in the
  database, so the root Verilates `debayer_default_hdl_sv_wrapper` and the
  header happens to exist. The root therefore Verilates 19 tops it never
  instantiates (ten IP `default` block tops and nine sub-block `default`
  tops) out of 30.

The two are coupled: trimming the tops without file-granular compile selection
breaks the swept-in IP registrars; file-granular selection without trimming
leaves the surplus tops. Both must move together.

Wall-clock note: in the 2026-09-18 root build all 27 small tops Verilated and
compiled between 14:11:43 and 14:12:20; the model C++ compile ran 14:47 to
15:03. The surplus tops are a correctness and coherence issue, not a build-time
one. Expect well under a minute of saving.

## 2. Goals and non-goals

Goals:

- The C++ compile set of a build is exactly what its manifest contract names
  plus hand-written user sources. No subtraction list.
- A composing project Verilates only the tops it can instantiate: its own
  declared variants of foreign blocks, its own blocks' standalone labels that
  reachable instances select, and pair tops of its own pairs.
- An IP standalone build is unchanged in what it compiles and Verilates.
- `make newmodule`, the stale sweeps and gen stamping keep their current
  inputs (unfiltered rows, owned directories).

Non-goals:

- Changing where registrar files live. Per-assembler per-child anchoring in the
  assembler's project is correct and stays.
- Changing the vlRegistrar template or registrar Config modules.
- Changing SV/RTL discovery (`rtl.f`, `A2C_SV_FILES`), which is already
  reachable-filtered.

## 3. Design

### 3.1 Manifest: `A2C_SC_SRC_FILES` and `A2C_SC_USER_SRC_DIRS`

In `createBuildManifest.py`:

- Add a foreign-inclusive `scSrcFiles` set next to `moduleFiles`. `record()`
  adds `stem + '.' + ext` for every ext in `_CPP_GEN_EXTS` that is a compiled
  source (`cpp` only; `h` is not a compile input, `cppm` already goes to
  `moduleFiles`). Rows of all four modes contribute (block, registrar, context,
  project), the same rows `record()` sees today.
- Registrar rows: a foreign-owned `blockVlRegistrar` row is not recorded into
  `scSrcFiles` (it is still recorded into `dirs`, so the compile of the
  directory's Config modules is unaffected). This replaces `cppExcludeFiles`
  with the same ownership test the hardened interim uses.
- Emit `A2C_SC_SRC_FILES := ...` and delete `A2C_CPP_EXCLUDE_FILES`.
- Emit `A2C_SC_USER_SRC_DIRS := ...`: the subset of `scSrcDirs` whose layout
  segment is flagged as holding user-authored sources. Add a per-segment flag
  in `config/project.yaml` (`userSources: [model, tb]`, next to `buildGroups`).
  Evidence from the root build: the only hand-written `.cpp` swept in today are
  six files under `<ip>/model/` (the isp_vconv ref stages and awb grayworld
  helper). `base`, `registrar`, `fwInc` and the tbConfig directory hold only
  generated TUs.
- Keep `A2C_SC_SRC_DIRS` as is. It still feeds `-I` include paths, the module
  scanner candidates and `compdb`.

### 3.2 Makefile: `a2c-systemc.mk`

Replace

```make
CPP_SRC += $(foreach dir, $(PRJ_SRC_DIRS), $(wildcard $(dir)/*.cpp))
CPP_SRC := $(filter-out $(A2C_CPP_EXCLUDE_FILES),$(CPP_SRC))
```

with

```make
# Generated TUs: the manifest names exactly the files this build's contract
# compiles (foreign-inclusive; a reused IP's TUs for pairs or harnesses this
# build does not reach are not listed). Hand-written TUs: wildcard over the
# user-source segments and EXTRA_PRJ_SRC_DIRS.
CPP_SRC += $(wildcard $(A2C_SC_SRC_FILES))
CPP_SRC += $(foreach dir, $(A2C_SC_USER_SRC_DIRS) $(EXTRA_PRJ_SRC_DIRS), $(wildcard $(dir)/*.cpp))
```

`$(wildcard ...)` on the file list keeps a not-yet-scaffolded intended file
from becoming a missing prerequisite, mirroring `SC_GEN_FILES` in
a2c-common.mk. `PRJ_SRC_DIRS` keeps feeding `CPP_INCLUDES` and
`CPP_MODULE_CANDIDATES`. `A2C_SRC_DIRS` (toolchain common sources) is unchanged.
`compdb-capture` depends on `$(OBJ)` and follows automatically. Remove the
VL_DUT comment that says registrations are "discovered under A2C_SC_SRC_DIRS".

### 3.3 Verilated tops: instantiated variants only

Today block-mode `vlSvWrap` rows are created for every label in
`standaloneVariantDescriptors(block)` (every non-foreign, non-container-sourced
label the block declares), and `createBuildManifest` records all of them as
tops. Change the top recording, not the row creation, so `newmodule` and the
`vl_wrap` stale sweep still see every declared label:

- Persist the per-build active variant set. `calcRegistrarPairs` already
  computes `activeConfigs[blockKey]` (one entry per concrete Config a reachable
  instance selects, with `variant`). Persist `{blockKey: sorted({variant})}` as
  `ACTIVEVARIANTS` (bin config, beside `REGISTRARPAIRS`).
- In the vlTops loop, skip a block-mode row when
  `row['variant'] not in activeVariants.get(row['blockKey'], set())`, subject
  to the policy below. Registrar-mode rows (`vlSvWrapForeign`, `vlSvWrapPair`)
  are already per build and are unchanged.
- `svGenFiles` for owned tops must keep covering every declared label, so the
  owner keeps regenerating the wrapper it declares even when its harness does
  not instantiate it. Record the gen target from the unfiltered row and the
  top from the filtered one.

Policy decision (for the user): apply the filter to
(a) foreign-owned blocks only, or (b) every block.

Recommendation: (a). It is the exported-surface ruling applied to Verilation:
the owner is responsible for building every label it declares, and an
integrator builds only the labels it uses. Under (a) no IP standalone build
changes. Under (b) an IP declaring labels its own harness never instantiates
would stop Verilating them in its own build, which silently drops a lint and
compile check the owner may rely on.

### 3.4 What stays as is

- vlRegistrar template and `<child>VlRegistrar.cpp` content (already per
  build from `verifRegistrations`).
- `getStaleSegmentFiles`, retired/legacy sweeps, `make newmodule`: they consume
  the unfiltered rows for owned directories.
- Fix 1 (declarer guard) and fix 2 (`__ALL.a` merge).

## 4. Stages

### Stage 0: land the interim (today)

User reviews and commits the three-part interim in base. Builder pin, clone
sync, IP and root pins follow the usual flow. This unblocks the root VL_DUT
build now and gives the proper fix a green baseline to diff against.

### Stage 1: file-granular compile set (base)

1. `config/project.yaml`: add `userSources` segment flag (model, tb).
2. `createBuildManifest.py`: `scSrcFiles`, `A2C_SC_USER_SRC_DIRS`, drop
   `cppExcludeFiles`; the foreign-owned `blockVlRegistrar` test moves from
   "add to exclude" to "do not add to compile set".
3. `a2c-systemc.mk`: compile-set change of 3.2; comment updates.
4. Confirm on the root: regenerate (`rm -f isp_top.db && make db`), diff the
   old wildcard set against `A2C_SC_SRC_FILES + user dirs`. Expected delta:
   minus the nine pair registrars (already excluded) and minus the ten IP
   harness registrars `<ip>/registrar/<ip>VlRegistrar.cpp`. Nothing else.
   Note the harness registrars only drop out safely together with stage 2's
   top trimming or with them still Verilated; in stage 1 alone they merely
   stop being compiled, which is fine because nothing in the root references
   their registrations.
5. Confirm on one IP (debayer): the compile set is byte-identical to today's
   wildcard set.

### Stage 2: instantiated-variant tops (base)

1. `processYaml.calcRegistrarPairs`: persist `ACTIVEVARIANTS`.
2. `createBuildManifest.py`: filter block-mode tops per 3.3 under policy (a);
   keep `svGenFiles` on unfiltered owned rows.
3. Confirm on the root: `A2C_VL_TOPS` drops from 30 to 11
   (ten `isp_top_<ip>_isp_hdl_sv_wrapper` plus `isp_top_hdl_sv_wrapper`).
   `A2C_VL_TOP_<block>` map unchanged for the DUT top.
4. Confirm on debayer: `A2C_VL_TOPS` unchanged (policy a).

### Stage 3: tests (base)

1. `unittest/test_build_manifest.py`: its premise ("manifest reproduces the
   glob dir set") inverts for `.cpp`. Keep the dir-set gate for `-I` paths,
   SV dirs and vl_wrap dirs. Add a compile-set gate: for every example, each
   generated `.cpp` on disk under an owned `sc` segment is either in
   `A2C_SC_SRC_FILES` or is a `blockVlRegistrar` of a pair with no
   registrations (assert by reading `REGISTRARPAIRS` from the example's db via
   `projectOpen`); and every listed file exists. Keep the region-content gates.
2. `unittest/test_container_param_cross_project_vl.py` (customer/customer2
   over vendor): assert the customer manifest lists no vendor harness
   registrar TU and no vendor `default` top the customer does not instantiate,
   and that the customer build still selects its RTL leaf. This is the
   composed-root shape in miniature and already builds under VL.
3. `test_stale_registrar_cleanup.py`, `test_stale_vl_wrap_cleanup.py`,
   `test_inherit_vl_child.py`, `test_variant_two_integrators.py`,
   `test_transit_container_vl_wrapper.py`: run unchanged; they cover the
   sweeps and the pair tops that must not regress.
4. Full `make unittest` in base (sequential where tests mutate examples).

### Stage 4: rollout

1. User reviews and commits base; builder pin; sync the ten IP builder clones.
2. Regenerate each IP (`rm -f <ip>.db && make db && make gen`; expect no source
   changes, manifest only, `.gen/build.mk` is untracked) and run each IP
   regression with `REGR_USER_OPTS="-j1"`; compare against the recorded
   baselines (debayer 44/44, blc 30/30, gain 31/31, lsc 26/26, awb 28/30,
   ccm 22/30, lut 37/37, rgb_gain 31/31, csi2raw and vid2axis at their
   baselines).
3. Root: `make clean && make -j4 all VL_DUT=1` and the model build; confirm
   11 tops, no excluded-file variable, link.
4. Pin isp_shared and root; update
   `docs/bug28-opencv-helper-consolidation-assessment.md` findings 3 and the
   `composed-root-subblock-trampoline-variant` memory note.

## 5. Verification matrix

| Check | Where | Expectation |
| :--- | :--- | :--- |
| Compile set delta | root | minus 9 pair registrars, minus 10 harness registrars, nothing else |
| Compile set delta | each IP | empty |
| `A2C_VL_TOPS` | root | 11 |
| `A2C_VL_TOPS` | each IP | unchanged |
| `A2C_VL_TOP_<block>` | root, IPs | unchanged |
| Stale sweeps | `test_stale_*` | pass unchanged |
| Pair tops | `test_inherit_vl_child`, `test_container_param_cross_project_vl` | pass |
| Regressions | ten IPs | at baseline |
| Root VL_DUT | root rundir | links |

## 6. Risks

- **Contract change for every project.** Generated `.cpp` discovery moves from
  directory to manifest for all IPs. Mitigated by the stage 1 byte-identical
  compile-set check per IP and by the regressions.
- **Hand-written `.cpp` in a generated-only segment stops compiling.** None
  exist today in the eleven repositories. Document the rule in the
  `manage-build` skill: hand-written TUs go under `model/`, `tb/`, or
  `EXTRA_PRJ_SRC_DIRS`.
- **A row `record()` does not see.** Any generated `.cpp` produced outside the
  fileMap rows would fall out of the compile set. The stage 1 delta check on
  the root (47 directories, all owners) is the detector.
- **Policy (b) chosen instead of (a).** IP builds would change; needs the IP
  regressions to be re-baselined for Verilated coverage.
- **`ACTIVEVARIANTS` for blocks with zero reachable instances.** Exported or
  library leaves the owner never instantiates have no active variant; under
  policy (a) they are owner-side and unfiltered, so no change.

## 7. Effort

- Stage 1: about half a day including the root and debayer delta checks.
- Stage 2: about half a day.
- Stage 3: about half a day; the manifest test rewrite is the bulk.
- Stage 4: the usual rollout, dominated by ten IP regressions (about two
  hours wall clock at `-j1`).

Roughly two working days end to end.
