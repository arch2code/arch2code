# Plan: `addressGroup` Project Qualification

**Status: COMPLETE.** Stages 0 (less 0.3), 1, 2, 3, 4, 5 and 6 all **LANDED**.
Still open, all recorded and none blocking: R3 (per-context firmware namespacing —
the cure the Stage 2 gate stands in for), R4 (SystemVerilog behaviour derived, not
measured on Verilator), R5 (two physical copies of one logical project sharing one
qualified key — believed correct, untested), R6 / R7 (adjacent defects, separate
reports), 0.3 (authored-YAML migration size, unsized — informational), and the
`UnboundLocalError` on `parent_interface_port` for a dispatch-tree-root router with
no upstream feed (pre-existing, reported in Stage 3, deliberately not fixed).

**Citation provenance:** every `file:line` was re-derived from the working tree on
2026-08-07. That tree is `HEAD = 23828e0` plus staged, uncommitted content, which
shifts `pysrc/processYaml.py` by roughly +26 lines relative to `HEAD`. Line
numbers drift on the next edit; the **symbol names are the durable anchors**.

**Provenance of the design.** The defect was written up by an earlier agent in
`~/bug-addressgroup-global-namespace.md`. That report is accurate in substance and
every claim in it was verified against the tree, but **it is a statement of the
problem, not an approved design**, and its "suggested fix" section carries no
authority here. The design in §2 is the authoritative statement. The
`(projectName, group)` key shape was chosen by the user; the firmware collision
in §4 and the rejection of outward fall in §3 are findings from this analysis.

---

## 1. The Defect

`AddressGroups` is a single flat, process-global dictionary keyed on the bare
authored group string. Every other schema object is context-qualified. Two
independently authored projects that each name their only address group `top`
therefore cannot be composed: `make db` fails with a duplicate-declaration error.

**The error is correct and must not be relaxed.** `generateAddressEnums`
(`pysrc/processYaml.py:5237`) folds instances from *all* contexts into one group
by bare name, so removing the duplicate check would silently share one address-ID
counter and one enum between unrelated projects. The defect is in the **key**.

Current state, for orientation:

| Element | Location |
| --- | --- |
| Duplicate-declaration check | `pysrc/processYaml.py:6852` |
| Four parallel dicts keyed on bare `group` | `:6876-6879` (`counterGroup`, `counterGroupControl`, `counterData`, `addressControl`) |
| Declaring provenance already on the row | `:6869` (`varTypeContext`), `:6873-6874` (`_declaringBlock`, `_declaringFile`) |
| Reference resolution (parse-time) | `_auto_addressGroup`, `:7094` |
| ID allocation and overflow check (parse-time) | `_auto_addressID`, `:7102` |
| Decoded-span check | `:4490-4492` |
| Enum emission and `varType` injection | `:5243`, `:5251-5269` |
| Router-block pairing by declaring file | `:4517-4519` |

---

## 2. The Design

### 2.1 Re-key on `(projectName, group)`

The `AddressGroups` registry key becomes the tuple `(owningProjectName, group)`.
Diagnostics spell it `owningProjectName::group`, for example `isp_lut::top`.

A tuple rather than a joined string, because it makes a string split impossible
by construction — `builder/base/CLAUDE.md` forbids string processing for lookup —
and because the same identity problem is already solved with a tuple key at
`pysrc/projectScan.py:47-49` (`logicalKey`). `ADDRESS_CONFIG` is persisted with
`bin=True` (`:4554`), so a tuple round-trips without encoding.

### 2.2 Resolution rule

> A group reference resolves to the group of that name declared in the same
> project as the referring file. If there is none, that is an error.

The owning project of a declaration is the project owning the declaring YAML file.
The owning project of a reference is the project owning the referring YAML file.

### 2.3 No new schema field

The information is already persisted twice over, so **this design adds no column
and makes no schema change**:

- `CONTEXTOWNINGPROJECT` is a persisted config blob, written at
  `pysrc/processYaml.py:3680` and reloaded at `:469` inside the read-only
  constructor at `:450`. Every generator and view already holds the
  context-to-project map.
- **Every schema row already carries `_context`.** `config/schema.yaml:6` states
  it as a global invariant: "all tables have field named `_context` which is the
  relative filename that the entry is defined." So any row's owning project is
  `contextOwningProject[row['_context']]`.
- Group rows already carry `_declaringFile` (`:6874`), so the declaring side
  resolves the same way.
- At parse time nothing needs storing at all: `_auto_addressGroup` already
  receives `yamlFile` in its signature, so it can resolve the referrer's project
  as it resolves the reference.

This is the established house pattern, not a new one. `:4517-4519` already pairs a
router block to its group with `blockRow['_context'] == groupRow['_declaringFile']`,
and its comment states the purpose: "so composed builds with same-named blocks in
different files stay distinct." The same problem was already solved for blocks by
comparing the declaring file rather than by adding a column.

Were a field ever needed, the house spelling is `projectName`
(`config/schema.yaml:340`, `:346`). None is needed.

### 2.4 The duplicate error narrows

It fires when one project declares the same group name twice. Two projects each
declaring `top` becomes legal. The diagnostic must name both declaring blocks,
both declaring files, and the project.

### 2.5 Authored YAML does not change

Users keep writing `addressGroup: top`. No migration, no `yamlFormat` bump.

### 2.6 What stays bare, deliberately

This is the part most worth scrutiny, because it is what keeps the change
output-neutral **and** what creates the second defect in §4.

- **`varType` and `enumPrefix` keep their authored values.** The generated enum
  stays `addr_id_top` with `ADDR_ID_TOP_*` members. Renaming them is precisely
  the churn this fix exists to avoid.
- **The stored and view-exposed `addressGroup` value stays bare.** Two existing
  tests assert it (`unittest/test_addrctl_single_router_one_reg.py:68-69`,
  `unittest/test_addrctl_ip_test_view.py:69-70`).
- The group name reaches generated text in exactly **one** place: the enum
  description comment built at `:5243`. It must stay bare or every project's
  output shifts and the byte-identity gate becomes meaningless.

### 2.7 Move the instance filtering into the view

`templates/systemc/constructor.py:551-554` filters instances by comparing bare
group names, and does so by walking `prj.data['instances']` inside a template.
That is both a layering violation under `builder/base/CLAUDE.md` and precisely the
code that breaks under composition. Its inputs come from a `projectOpen` view at
`pysrc/processYaml.py:2143-2144`.

The view must resolve the qualification and hand the template an
already-filtered, already-sorted instance set. The template stops deriving the
relationship. `:2144` also reads `addressBlock.get('addressGroup')` where
`config/schema.yaml:293` declares `addressGroup: required`, so that fallback goes
at the same time.

**Also in scope, on review (Stage 6.3):** `constructor.py:549`
(`addressGroupData.get('registerDecoderPort') or 'apb'`) is a genuine contracted-
field violation. It was initially scoped out as unrelated; that was wrong, because
it sits inside `addressDecoder`, the function this change rewrites, four lines
above the rewritten loop. `addressGroupData` is `dict(addressBlock)` from `:2143` —
a block's `addressBlock:` row, never an `AddressGroups` row — so the comment above
it described a structure that cannot reach that line. `registerDecoderPort` is
`optional(apbReg)` (`config/schema.yaml:298`) and always materialises; the fallback
substituted `'apb'` against a schema default of `'apbReg'`, which if it ever fired
would emit `apb_<instance>` while `config/postParseRegisterPorts.py` named the port
`apbReg_<instance>`. Now a direct read, comment deleted.

---

## 3. Rejected Alternative: Outward Fall to Ancestor Projects

The option was to fall back, when the referring file's own project declares no
group of that name, to the parent project and onward to the root, taking the
first match. **Rejected.**

**Primary reason — it defeats the purpose of the change.** A child IP that names a
group it does not declare has hard-coded a name owned by its parent. That IP is no
longer independently reusable, which is the property this whole change exists to
establish. The case cannot legitimately arise from below.

**Supporting reasons:**

- **It does not work at parse time anyway.** Reference resolution and ID
  allocation are parse-time (`:7094`, `:7102`), and `processYamls` (`:6028-6080`)
  processes files in include-dependency order, so a child's files are parsed
  *before* its parent's. An ancestor's group is registered *after* any child row
  that would fall outward to it, so the fall finds nothing. Making it work
  requires moving instance-to-group binding and ID allocation into a post-parse
  pass that reproduces the current allocation order exactly — real output-change
  risk on every project that allocates address IDs.
- **The machinery does not exist.** `ScanResult` (`pysrc/projectScan.py:41-68`)
  carries file-to-project ownership but no ancestry chain; `_assignOwnership`
  (`:318-375`) computes a BFS depth and a per-provider boundary set and then
  discards both. Outward fall needs a new persisted ancestry chain.
- **Nothing in the tree needs it.** In every project here, each `addressGroup:`
  reference sits in the same file as its `addressBlock:` declaration, so outward
  fall would be a no-op on the entire corpus.
- **The reported ten-IP case does not need it.** The parent declares the ten IP
  instances in its own root-owned file, so they qualify to the root and land in
  the root's group with no fallback.

**This rejection is not conditional.** A reference that reaches out of its own
project for a name it does not own is incoherent regardless of what any particular
project's file layout happens to look like today. So if an IP-owned file somewhere
*does* name a group its project does not declare, that is a defect in that YAML to
be fixed by moving the declaration or the reference — it is not evidence that
outward fall should exist. The Stage 0 check on the ISP layout is therefore
informational: it tells us how much authored YAML needs correcting, not whether
this design is right.

**Consequence:** an unresolved reference is an error. The diagnostic must name the
group, the referring file and its owning project. It may also list projects that
declare a group of that name, which is what makes the error actionable in the
composed case this change enables — but **only as a "parsed so far" observation.**
The check is parse-time and `counterGroup['AddressGroups']` fills as each file is
parsed, so at the moment of the check a later-processed project's declaration is
not yet registered. The diagnostic must therefore never assert a build-wide
absence; when the observed list is empty it says nothing about the name at all.
See Stage 6.1.

---

## 4. Second Defect: the `varType` Collision (mandatory, same merge)

Because §2.6 keeps `varType` bare, two projects both naming a group `top` will
both emit `enum addr_id_top` — and the firmware surface has no per-context
separation to keep them apart.

Verified:

- **Firmware uses one flat namespace for every context.**
  `FW_NAMESPACE = 'fw_ns'` (`pysrc/intf_gen_utils.py:481`), applied by
  `wrap_fw_namespace` (`:644`). The model side, by contrast, is safe:
  `wrap_module_namespace` (`:638`) exports each context into a project-qualified
  namespace.
- **Firmware headers include each other across project boundaries.**
  `examples/ip_test/top/fw/ip_topIncludesFW.h:8-13` includes the `src`, `ipLeaf`,
  `ip` and `ipBridge` firmware headers. Include guards are per-file, so two files
  each defining `addr_id_top` both arrive.
- **The build compiles every `.cpp` in every manifest source directory.**
  `include/make/a2c-systemc.mk:85-86` globs `$(wildcard $(dir)/*.cpp)` over
  `PRJ_SRC_DIRS`, and the composed manifest `examples/ip_test/.gen/build.mk`
  lists five separate `*/fw` directories.
- **No guard exists.** Nothing compares two groups' `varType` or `enumPrefix`.
  Every example in the corpus hand-picks distinct names, so there is no precedent
  either.

Two failure modes:

1. **Same translation unit** — a hard C++ redefinition error. Loud, and therefore
   the acceptable outcome.
2. **Different translation units, different enumerator values** — ill-formed, no
   diagnostic required. Since these values are address IDs, the silent result is a
   wrong address.

Today's duplicate-group error is the only thing preventing a build from ever
reaching either. **Narrowing it without a guard trades a loud database-time error
for a possibly silent one.**

**Therefore, mandatory and in the same merge as the re-keying:** a `projectCreate`
check that errors when two `AddressGroups` entries resolve the same `varType` or
the same `enumPrefix`, naming both groups in `::` spelling, both declaring blocks,
both declaring files, and both projects. Model the diagnostic on the existing
identity-uniqueness check at `:3743-3756`, which solves the structurally identical
problem for context module and package names.

Two properties of the gate:

- It is **build-wide, not per-include-closure**. A per-closure gate would miss
  failure mode 2, which is the dangerous one.
- It is a **no-op on every existing project**, since all corpus `varType`s are
  distinct. It also closes a pre-existing hole: two *differently named* groups
  sharing one `varType` is already broken today and unchecked.

**This is a gate, not a cure.** The real fix is per-context namespacing on the
firmware surface, matching what the model side already does. That is a large
change to the `.h`/`.cpp` firmware contract, it touches user firmware, and it is
out of scope here. See R3.

---

## 5. Scope Summary

| Change | Location |
| --- | --- |
| Registry key becomes `(projectName, group)` | `_post_registerAddressBlock`, `:6876-6879` |
| Duplicate check narrows to within-project | `:6852` |
| Reference resolves by referring file's project; precise error otherwise | `_auto_addressGroup`, `:7094` |
| Consumers form the tuple from `_context` / `_declaringFile` | `:4490`, `:5251-5269`, `:7108-7115` |
| `varType` / `enumPrefix` collision gate (new) | beside `generateAddressEnums`, `:5237` |
| View resolves qualification, supplies `routedInstances` | `getBDAddressDecode` |
| Template stops walking `prj.data` | `templates/systemc/constructor.py::addressDecoder` |
| Bare-group fold in the template retired | `templates/systemc/constructor.py::addressDecoder` |

No schema change. No YAML migration. No new persisted column.

---

## 6. Stages

### Stage 0 — Baseline (no source change) — DONE

**Result.** `debayer` baseline: `make clean && make -j gen` clean, build clean,
`./build/run debayer --verbosity=medium` printed `No error` at exit 0.
`make pipeline-test` green in 9m16s. Parallel-runner suite count was 89.
**0.3 not sized** — the reporting workspace is not available in this tree, so the
authored-YAML migration count is unknown; it is informational and does not gate
the design.

**Corpus baseline: superseded — see "Authoritative A/B" below.** This stage
recorded "1438 generated files" and Stage 3 recorded a "1329-file base+pro
corpus"; neither stage wrote down its scope, so the two numbers are not
comparable and neither is reproducible from the record. Both are replaced by the
single scope defined in "Authoritative A/B", which covers all stages at once.

0.1 Capture the A/B baseline: full corpus `make clean && make -j gen`, then a
byte snapshot of all generated files, excluding `.gen/` (which the *build*
writes, not `gen`, so including it makes the snapshot build-state dependent).
Record the file count.

0.2 Record `debayer` diffstat, and the current parallel-runner suite count
(`unittest/run_all_tests_parallel.sh:66-70` hard-codes it).

0.3 **Size the authored-YAML migration** (informational, does not gate the design —
see §3 and R1). Count rows across the reachable projects that name a group their
own project does not declare. Each is a one-line YAML fix, not a reason to change
the resolution rule. Skip if the workspace is unavailable and record it as unsized.

**Gate:** baseline recorded.

### Stage 1 — Re-key and narrow the duplicate error — DONE

**Landed as designed.** The registry key is the tuple `(owningProjectName, group)`
in all four dicts; `addressGroupLabel()` (module scope, beside
`qualifyModuleIdentity`) is the `project::group` diagnostic spelling. Consumers
form the tuple from the row's `_context` (`calcAddresses` space check,
nested-decoder containment, `generateAddressEnums`) or from `yamlFile`
(`_auto_addressGroup`, `_auto_addressID`, `_post_registerAddressBlock`).

**Beyond the listed scope, inside the touched consumers:** the dead
`decoderInstance` fallback in `generateAddressEnums` (a legacy-`addressControl`
path that can no longer be reached, and a presence test on a contracted field) was
collapsed to a direct `varTypeContext` read; the adjacent
`instData.get('addressGroup', None)` became a direct read. The pre-existing
nested-decoder diagnostic now spells both groups `project::group`, so
`test_error_nested_decoder_overflow.py`'s substring was updated to match.

1.1 Change the four dicts at `:6876-6879` to the tuple key. Resolve the declaring
project from `yamlFile` via `contextOwningProject`.

1.2 Narrow `:6852` to within-project, with the diagnostic from §2.4.

1.3 Update `_auto_addressGroup` (`:7094`) to resolve by the referring file's
project, with the unresolved-reference diagnostic from §3.

1.4 Update every consumer to form the tuple: `:4490`, `:5251-5269`, `:7108-7115`.
Each has the row's `_context` or the group's `_declaringFile` in hand.

**Gate:** A/B byte-identical against Stage 0; suite green; `make pipeline-test`;
`debayer` build and run; second `make gen` idempotent.

### Stage 2 — The `varType` / `enumPrefix` collision gate — DONE

**Landed as designed**, in the same change as Stage 1.
`validateAddressGroupEnumIdentity()` sits beside `generateAddressEnums` and is
called immediately before it, so the collision is rejected before any enum is
emitted. Build-wide, one dict per field, first collision reported with both
`project::group` keys, both declaring blocks and both declaring files. No-op on the
whole corpus (A/B byte-identical).

2.1 Add the build-wide gate per §4, beside `generateAddressEnums`.

2.2 Record in a behaviour comment that it also closes the pre-existing
same-`varType`-different-name hole.

**Must land in the same merge as Stage 1.**

**Gate:** A/B byte-identical (the gate is a no-op on the corpus); suite green plus
the new negative fixture from Stage 4.

### Stage 3 — View and template layering — DONE

**Landed as designed.** `getBDAddressDecode` now resolves the router's group as
`(contextOwningProject[blockRow['_context']], addressBlock['addressGroup'])` and
publishes `addressDecode['routedInstances']`: the instances whose own context
resolves to that same pair, sorted by `addressID` (the address slot). The
`addressBlock.get('addressGroup')` fallback became a direct read.
`templates/systemc/constructor.py::addressDecoder` consumes the field and no
longer touches `prj.data`; membership in the view-supplied `instanceWithRegApb`
is now keyed on `instanceKey` explicitly rather than on the dict key it happened
to iterate. `addressDecode['addressGroup']` stays (bare, per §2.6) — two suites
assert it.

**This was a correctness fix, not only a layering fix.** Stages 1/2 qualified the
database and the firmware enums, but the template still selected channels by
comparing bare group names against the flat `prj.data['instances']`. Proven on the
Stage 4 fixture: pre-change, `childADecode`'s emitted channel array was
`[&apbReg_uChildBLeafX, &apbReg_uChildALeafX, &apbReg_uChildA,
&apbReg_uChildBLeafY, &apbReg_uChildALeafY, &apbReg_uChildB]` — six slots drawn
from all three projects, naming ports that do not exist on that router. Fixture
4.1 asserts on the firmware enum and passed throughout, so it could not have
caught this; the new suite is what closes that gap.

**Beyond the listed scope, inside the touched function:** the nullptr gap-padding
in `addressDecoder` was removed. Its `addressID` cursor was never advanced past
its `addressID = 0` initialisation, so `instanceData['addressID'] < addressID`
could not be true for a non-negative slot index; independently, `_auto_addressID`
advances the group counter by `addressMultiples` for every routed instance, so
slot indices are contiguous and there is no gap to pad. The pre-change run above
confirms it: six same-group instances with duplicated IDs 0,0,0,1,1,1 emitted no
padding at all.

3.1 The view at `:2143-2144` resolves the qualification and supplies the filtered,
sorted instance set. Remove the `addressBlock.get('addressGroup')` fallback.

3.2 `templates/systemc/constructor.py:551-554` consumes the view field and stops
walking `prj.data`.

3.3 Decoder-channel regression fixture, `test_addrgroup_composed_decoder_channels.py`
(companion to 4.1, same composed fixture): asserts each child project's router
emits exactly its own two leaves in its own slot order. Proven to FAIL against the
pre-change template and pass after. Registered in `ADDRCTL_TESTS`; the
parallel-runner drift guard moved 93 -> 94.

**Gate:** A/B byte-identical (this stage's own run reported a "1329-file base+pro
corpus" without recording its scope — **superseded** by the single scope in
"Authoritative A/B" below); `Ran 94 suites: 94 passed, 0 failed`;
`make pipeline-test` rc=0; `debayer` clean gen (diffstat unchanged at 25 files /
70 insertions / 244 deletions), build and run `No error` at exit 0; second
`make -j gen` idempotent.

**Finding, not fixed here:** the fixture's *root* router cannot have its block
module generated at all — `addressDecoder` raises `UnboundLocalError` on
`parent_interface_port` because the dispatch-tree root in a container with no
`registerPorts:` has neither an upstream connection nor a connectionMap (see
`postParseRegisterPorts.py`, "A primary nested router in a plain container has no
boundary feed"). Pre-existing and independent of this stage; the template should
fail loud instead. The new suite therefore asserts on the two child routers.

### Stage 4 — Regression fixtures — DONE

**Landed.** Fixture tree `unittest/fixtures/addrgroup-qualification/` plus the
shared harness `unittest/_addrgroup_qual_helpers.py`. Four suites, all four proven
to FAIL against the pre-change generator and pass after:

| Case | Suite |
| --- | --- |
| 4.1 positive | `test_addrgroup_composed_sibling_groups.py` |
| 4.2 within-project duplicate | `test_error_addrgroup_duplicate_in_project.py` |
| 4.3 enum identity collision (`varType` **and** `enumPrefix`) | `test_error_addrgroup_vartype_collision.py` |
| 4.4 unresolved reference | `test_error_addrgroup_unresolved_reference.py` |

The fixture composes **three** projects that each declare a group named `top`
(rootProj plus sibling childAProj / childBProj) rather than two: the root needs its
own router to be the dispatch-tree root, so making its group `top` as well costs
nothing and covers the parent-plus-children shape from §3. 4.1 is a generator run,
not a column read: it scaffolds and generates each project's firmware header and
asserts each carries its own `addr_id_*` enum with IDs restarting at 0 (a shared
counter would number the six routed slots 0..5). Child-owned artifacts are produced
by a run whose PROJECTNAME is flipped on a copy of the same composed database - the
`test_nested_ownership.py` ownership-gate pattern. Registered in `ADDRCTL_TESTS`;
the parallel-runner drift guard moved 89 -> 93.

**Location:** `unittest/`, not `examples/`. The flat-file
`_addrctl_helpers.make_project()` cannot express a composed project, so follow the
`test_nested_ownership.py` copytree pattern with a fixture under
`unittest/fixtures/addrgroup-qualification/`. No composed fixture in the tree
currently contains any address control.

4.1 **Positive:** two sibling sub-projects each declaring a group named `top`
with distinct `varType`s. Must reach a database and allocate independent ID
counters. This is the case that fails today.

4.2 **Negative — within-project duplicate:** one project declaring `top` twice.
Must still error.

4.3 **Negative — `varType` collision:** two projects each declaring `top` with the
*same* `varType`. Must error with the Stage 2 diagnostic. This is the §4 guard.

4.4 **Negative — unresolved reference:** a row naming a group no project of its own
declares. Must produce the §3 diagnostic, including the list of projects that do
declare that name.

4.5 Register in the `ADDRCTL_TESTS` array (`unittest/run_all_tests.sh:249-289`)
and bump the parallel-runner drift guard. **Read the guard, do not assume the
count.**

**Gate:** every new fixture fails before its stage and passes after; full suite
green.

### Stage 5 — Documentation — DONE

**Landed.** Two authoring constraints are now user-facing: the project-scoped
resolution rule (§2.2, with the reusable-IP corollary from §3) and the build-wide
`varType` / `enumPrefix` uniqueness gate (§4) — stated *with its mechanism*, since
a rule given without the `fw_ns` flattening behind it invites a workaround.

5.1 **`plan-address-control-refactor.md`** — new "Amendment 2026-08-07" section
recording the `(projectName, group)` registry key, the within-project duplicate
check, project-scoped reference resolution, how consumers form the tuple, and why
`varType`/`enumPrefix` stay bare and are gated instead. The three places that
stated the flat key (§1.2's `_post_registerAddressBlock` note, Stage 4 step 1,
Stage 5.3's diagnostic list) each carry an inline amendment pointer, so a future
reader cannot reintroduce it from any one of them.

5.2 **`plan-address-control-test-coverage.md`** — new topology rows T6.1 / T6.2
(composed sibling groups, composed decoder channels), new
"`addressGroup` qualification diagnostics" error subsection E5.1 / E5.2 / E5.3,
six coverage-map rows, an E1.4 narrowing note, and a status addendum. Every row
names the fixture file actually on disk.

5.3 **Skills.** Both discuss group naming, so both carry the rules.
`design-register-decode.md` gets a "Group naming — two build-wide constraints"
subsection in §5 (the `addressBlock:` field reference) plus four appendix rows
quoting the real diagnostics: the within-project duplicate, the unresolved
reference, the enum-identity collision, and the Stage 6.2 empty-`routedInstances`
generation-time error. `manage-address-space.md` gets two bullets in its step-2
"Address groups (per-block schema)" list. No plan filenames or stage numbers appear
in either — the skills are user-facing.

Skills are **copied**, not symlinked, to `.claude/skills/<name>/SKILL.md` (and
`.gemini` / `.opencode` / `.agents`) by the `agents-setup` target in
`include/make/a2c-agents.mk`, so the sources above do not reach a deployed agent
until `make agents-setup` is run from the repo root. `cursor-setup` does the same
for `.cursor/skills/`. **Deployment is the user's call and was not run.**

5.4 **Source report marked resolved.** `~/bug-addressgroup-global-namespace.md`
(outside the repo) carries a resolution header pointing at this plan.

### Stage 6 — Review fixes on the landed change — DONE

Four findings raised against Stages 1-4 after they landed. All four are inside
code this change wrote or rewrote.

6.1 **The unresolved-reference diagnostic asserted a falsehood.**
`_auto_addressGroup` printed "no project in this build declares 'X'" whenever its
observed list was empty. The check is parse-time and
`counterGroup['AddressGroups']` is populated as each file is parsed, so a project
whose `addressBlock:` declaration lives in a later-processed file is not yet
registered. Demonstrated on the Stage 4 fixture with both child declarations
renamed: pre-fix printed "no project in this build declares 'top'" while
`rootProj` (parsed last) does declare it.

The check stays parse-time — the `_auto_addressID` allocation immediately below
depends on it — so the wording changed, not the placement. The negative branch is
gone; the list is now rendered only when non-empty and is spelled "Projects
declaring a group named 'X' parsed so far in this build: [...]", which claims no
build-wide census. Group, referring file and owning project are unchanged. The
Stage 4.4 fixture's asserted substrings all survive the rewording unchanged.

6.2 **`routedInstances` did not restrict to this build's design tree.**
`getBDAddressDecode` filtered on the `(project, group)` tuple but not on
reachability, so a referenced child project's standalone-harness instances — which
are parsed into the same database but do not descend from the active `topInstance`
— were eligible. The filter `if instanceKey in self.reachableInstances` now applies,
matching the established rule in the sibling emitter
`templates/systemc/includes.py::includeAddresses`.

The input is real, not hypothetical: `uIp/../../ip/yaml/ipTop.yaml` is
routed-but-unreachable in `examples/ip_test/ip_test.db`,
`examples/simple_ip/simple_ip.db` and `examples/ip_test/bridge/ipBridge.db`. It
produced no wrong output only because that router's block module is child-owned
and the parent build's ownership gate skips rendering it — an accident, not a
guarantee; a same-project unreachable routed instance would have been emitted as a
spurious channel slot.

The filter can empty `routedInstances`, and the trailing-comma fixup in
`addressDecoder` would then pop the `,decoder(...{` line itself and silently emit
malformed C++. So the empty case now fails loud in the view: `printError` naming
the router block and its `project::group` label, then
`exit(warningAndErrorReport())`. It does not fire anywhere in the corpus.

6.3 **`registerDecoderPort` contracted-field fallback** in
`templates/systemc/constructor.py::addressDecoder` — see §2.7. Now a direct read;
the comment describing an unreachable legacy shape is deleted. An empty *authored*
value would belong in `projectCreate` validation on the `addressBlock:` row, not
here; not added.

6.4 **Stale `ADDRESS_CONFIG` comments.** `ADDRESS_CONFIG` (`:4602`) is write-only
(§8). Two comments asserted a read that does not exist and were corrected: the
`getBlockData` call-site comment claiming routers without an authored
`addressBlock` get an equivalent view from `ADDRESS_CONFIG` (`getBDAddressBlockView`
performs no such read), and `loadProjectAddressPolicy`'s claim that the allocator
and firmware-header generator consume the blob (they consume the counter state).
Two further docstrings described writes into the "`ADDRESS_CONFIG` entry" — true,
but they name a persisted blob nothing reads; they now name `self.addressControl`,
the in-memory dict they actually populate.

**Deliberately not fixed, reported only:** the `UnboundLocalError` on
`parent_interface_port` for a dispatch-tree-root router with no upstream feed
(pre-existing, see Stage 3); `templates/systemVerilog/apbDecodeModule.py:45`'s dead
local; and `counterData['AddressGroups']` being write-only.

**Gate:** the authoritative A/B below; `Ran 94 suites: 94 passed, 0 failed`;
`make pipeline-test`; `debayer` gen + build + run; second `make -j gen` idempotent;
the 6.1 diagnostic demonstrated in both parse orderings.

### Authoritative A/B (single scope, all stages)

One measurement covering Stages 1-4 and 6 together. It replaces the Stage 0 and
Stage 3 corpus numbers, which each used an unrecorded scope.

**Scope — regeneration.** Every example project in `builder/base/examples` and
`builder/pro/examples`, each rebuilt from a deleted database:

- the 18 projects with a project `Makefile` (`shared.mk` `gen` target), children
  before parents: `ip_test/{common,ip,bridge}`, `ip_test`,
  `simple_ip/{common,ip}`, `simple_ip`, `apbDecode`, `axi4sDemo`, `axiDemo`,
  `helloWorld`, `hierVlDemo`, `mixed`, `nested`, `pySocket`, `simple`, `xif`,
  `pro/examples/lmmiDemo` — `make clean` then `make -j8 gen`;
- the 2 SV-only examples with no project `Makefile`, `hierInclude` and `inAndOut`
  — `make -C arch clean`, `make -C systemVerilog clean`, `make -C systemVerilog lint`
  (lint is what drives their SV generation).

`pySocket` is **included**; it is `yamlFormat: 2` and gens clean.

**Scope — snapshot.** Every file under those two example trees except: anything
under a `.gen/` directory (the *build* writes `.gen/cpp-modules.mk` and
`.gen/*.scgen`, so including it makes the snapshot build-state dependent), the
sqlite databases, `*.log`, `compile_commands.json`, `.clangd`, and `build/`,
`obj_dir/`, `gv_out/`. Authored sources are inside the snapshot on purpose: they
are invariant across A and B so they cannot mask a difference, and it removes any
judgement about which files "count" as generated.

**Count: 1443 files, of which 528 carry a `GENERATED_CODE` marker.**

**Result: A/B byte-identical, 1443/1443.** A = `HEAD` (`cb24548`), the whole change
reverted by restoring `pysrc/processYaml.py` and
`templates/systemc/constructor.py` in the worktree only (`git show HEAD:<path>`,
never `git checkout`, so the submodule index is untouched). B = the working tree
with all stages plus Stage 6. Both regens returned rc=0 for all 20 projects, and
the B snapshot reproduced exactly across two clean regens.

**Reconciliation (INFERRED — neither earlier stage recorded its scope).** Measured
under this snapshot's exclusions on the current tree: base+pro = 1443; base only =
1380; base+pro less `pySocket` = 1382; base only less `pySocket` = 1319; marker
subset = 528; marker subset plus `.gen` stamps = 1063. Stage 0's **1438** is
consistent with this scope (base+pro, all files, `.gen` excluded) on a tree five
files smaller — its "pySocket excluded" note refers to regeneration, not to the
snapshot. Stage 3's **1329** is consistent with the base-examples-only,
`pySocket`-excluded variant (1319 today). Neither is exactly reproducible; both
entries are superseded rather than reconstructed.

---

## 7. Risks

**R1 — Some authored YAML may need correcting.** Per §3 the resolution rule is not
negotiable, so the open question is only how much existing YAML violates it. Any
row naming a group its own project does not declare will now be a hard error where
before it silently bound to whatever project happened to declare that name first.
That is the intended behaviour, but it means the ISP integration may need
declarations or references moved. **Not a design risk; a migration-effort unknown.**
Stage 0's check sizes it. The clear error message required by §3 — naming which
projects do declare the name — is what makes each instance a one-line fix.

**R2 — Output neutrality: MEASURED, closed.** The claim rested on tracing every
consumer and on the group name reaching text only at `:5243`. The authoritative
A/B in §6 proves it: 1443/1443 files byte-identical between `HEAD` and the working
tree over the whole base+pro example corpus. Stage 6.2's reachability filter was
the one change that could legitimately have moved output; it did not, because the
only routed-but-unreachable instance in the corpus belongs to a router whose block
module the parent build does not render.

**R3 — The `fw_ns` flattening is the underlying disease.** Stage 2 gates the
symptom. Per-context firmware namespacing is the cure, is out of scope, and will
be wanted. Recorded so the gate is not mistaken for a fix.

**R4 — SystemVerilog behaviour is derived, not measured.** SV packages are
project-qualified, but generated code wildcard-imports several into one scope.
Ambiguity is an error only on unqualified reference and nothing generated
references the address enum, so it is probably benign. Not confirmed on Verilator.
Stage 4.3's fixture should measure it.

**R5 — Two physical copies of one logical project share one qualified key.**
Qualification is by `projectName`, and the scanner reconciles multiple physical
copies onto one master. Two copies of `isp_lut` therefore map to one
`(isp_lut, top)`. This is believed correct — they are one logical project — but
untested: `unittest/fixtures/multi-copy` exists and would be the natural home,
and it contains no address control today. Cheap to add in Stage 4.

**R6 — `getBDAddressBus` resolves the register-bus interface by a global name
match** (`pysrc/processYaml.py:3000`, diagnostic `:3001-3004`). It scans
`self.data['interfaces'].values()` across every context for a matching
`interface` name, so two composed projects declaring the same register-bus
interface name are the same class of hazard as this defect, in an adjacent path.
The same line also uses `x.get('interface')` where `interface` is a contracted
field. Untouched here; worth a separate report.

**R7 — A child project's `instanceGroups:` / `addressObjects:` are silently
ignored.** Only the root `project.yaml` is read by `loadProjectAddressPolicy`
(`pysrc/processYaml.py:5385`).
This is what makes `AddressGroups` the only section affected by this defect, so it
is fine for this change, but it is a latent surprise for a composed build.

---

## 8. Notes on the Existing Test Corpus

`examples/ip_test` does **not** exercise this defect. Its three groups (`ipStd`,
`bridge`, `top`) are distinct by hand, and `examples/ip_test/bridge/ip` is a
**symlink** to `../ip`, so the repeated `ipStd` declaration is one file rather than
a latent second declaration.

`ADDRESS_CONFIG` (`:4602`) is **write-only** — there is no reader anywhere in the
tree. Changing its key shape is therefore free. The four comments around it are
corrected in Stage 6.4.

An optional three-line change would give this defect template and runtime
coverage in the example corpus: rename the `ipStd` group to `top` in
`examples/ip_test`, making two of its groups collide by name. That is a **user
decision**, not part of this plan, because it changes a shared fixture that other
plans' tests read.
