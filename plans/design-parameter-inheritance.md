# Authoring Guide: Parameter Inheritance

**Who this is for.** An engineer authoring a design in YAML. It states what the YAML looks
like, what is generated from it, and what is allowed and what is not. It does not describe
how the generator works; that belongs to
[`plan-parameter-sharing.md`](./plan-parameter-sharing.md), which also carries the decision
history and the outstanding work.

**The rules section is normative.** Where the generator does not yet enforce a rule, the list at
the end of that section says so and names the plan step. §5 lists the two things that are not
covered at all, and is worth reading before putting an inherited parameter on a register-bus
router width.

---

## Rules (confirmed with the architect, 2026-09-07)

The point of parameterization is to let an author choose where each fact comes from without
stating it twice. There are three facts: a parameter's declaration, a block's use of it, and the
value an instance sees. Each has a small set of legal sources, and every rule below exists to keep
each source unambiguous. This section is the normative statement; the rest of this document
shows the YAML, and [`plan-parameter-sharing.md`](./plan-parameter-sharing.md) holds the history
and the evidence. The first draft was iterated with the architect rule by rule on 2026-09-07; each rule carries
the date it was confirmed or ruled, and the list at the end records where the tree has not
caught up.

Declaration.

1. A parameter is declared once, as an `ipParameters:` constant, and that one declaration is
   its identity everywhere it is reached. The declaring file may be any file, including a
   definitions-only file of a shared project that holds no `blocks:`, so that several IPs and
   several projects name one parameter (an image pipeline's `BITS_PER_PIXEL`). Nothing requires
   the declaring file, or the declaring project, to name the parameter itself. (Ruled and landed
   2026-09-07/08, plan step 12a.)
2. A block names the parameters it uses in `params:`. Each name resolves through the block's
   include scope to one declaration. Zero visible declarations is an error, and so is more than
   one. Visible means reachable from the block's own file through its include chain; a
   same-named declaration in a file the block does not reach is a different parameter, not a
   collision. The block's own file does not shadow an included declaration: two visible
   declarations of one name are two definitions, and are rejected however they are placed.
   (Confirmed 2026-09-07.)
3. A block's configuration is exactly the parameters it names. Anything derived from them is
   computed in the implementation, never configured. The derivation may be written once in YAML
   as an `eval:` constant; it is emitted as a computed value, never as a Config member, and may
   not itself be named in `params:`. (Confirmed 2026-09-07.)

Value.

4. An instance's values come from its container or from a variant, and a variant binds every
   parameter of its block, once each, from one of three sources:
   - a literal;
   - a constant visible in scope;
   - a parameter of the containing block, named by `containerParam:`. The names need not match,
     so this is also how a child parameter is renamed at the boundary. The container parameter's
     bound may not exceed the child's.
   Nothing fills in an omitted binding. The whole-container form, `inheritContainerParam: true`
   on the instance, sources every parameter of the block from the container's parameter of the
   same name, so the block's parameter set must be a subset of the container's; it names no
   variant and renames nothing, and it is confined to a container and child owned by one
   project. Across projects the child takes a declared variant whose bindings are
   `containerParam:`. `containerParam:` is the flexible form and `inheritContainerParam:` the
   same-project shorthand for the same-name subset case. (Ruled 2026-09-07.) Each shared name must
   also be the same `ipParameters` constant on both sides. A same-named child declaration with a
   smaller `maxValue` would otherwise pass the subset check and be sized below what the container
   can bind. Use `containerParam:` where the two must stay distinct declarations. (Ruled 2026-09-09.)

   How the factory selects a container-sourced child, in both forms alike: the child's C++
   type is a function of the container's Config, so the container names the concrete class as
   the template argument of `instanceFactory::createInstance` and forwards its own runtime
   variant label in place of a child label. The registry key is (child block, that forwarded
   label, the pair-qualified domain). An exact match, which is how a Verilated or tandem
   replacement registered per container variant is found, wins; otherwise the class named at
   the site is constructed. A child that names no variant therefore has an identity at the
   factory: its container's.
5. A variant is owned by the project that declares it. Its identity is (block, variant,
   declaring project), its name carries the project, and the declaring project emits it without
   touching another project's artefacts. (Confirmed 2026-09-07; landed as plan step 15 the same day.)
6. Any project may declare a variant of any block visible to it, whether or not it owns the block.
   (Confirmed 2026-09-07.) "Owns the block" means the project owning the block's declaring file, not the file
   holding its `ipParameters`; a declaration by the block's owner is native wherever the parameters
   are declared. (Ruled 2026-09-14.)

Selection.

7. An instance of a parameterized block selects its configuration either by naming a variant or
   by taking its container's whole configuration (`inheritContainerParam:`, rule 4's
   whole-container form). A named variant resolves through the instance's include scope, the
   include chain of the file holding the instance row, to one declaration. Zero or more than one
   visible declaration is an error, and the message names every declaring file. (Confirmed
   2026-09-07.)
8. A top instance is not parameterized. (Confirmed 2026-09-07.)

Guarantees.

9. The two ends of a connection are compared at the values their instances actually resolve, and
   a disagreement is a db-time error naming both sides.
10. Nothing falls back to a default silently. Where a source cannot be resolved, the build stops
    and says which rule failed. (Rules 9 and 10 confirmed 2026-09-07.)

Scope decides what is visible. Project decides who owns. The file a statement sits in decides
neither.

### Where the tree deviates today

Recorded so the iteration argues about facts. Dated 2026-09-07; delete each line as it closes.

- Rules 2 and 7, visibility: both say include chain. Every scoped lookup in the tree, the two
  scope checks included, sees a file, the files it includes, and the files those include, and no
  further (`GENERATOR_ARCHITECTURE.md` section 4 records the two-level flattening as deliberate).
  A declaration three includes away is reported as out of scope. RULED 2026-09-13: the rule stands;
  the 2026-09-08 `rtl.f` loss in `ip_test`'s bridge top was a tool defect (the file list walked the
  top file's scope instead of the closure over reachable RTL contexts' scopes) and is fixed as such.
  LANDED 2026-09-13 (`COMPILECONTEXTS`, renamed from `SVCOMPILECONTEXTS` 2026-09-14); the bridge top's workaround include is gone.
- Rules 5 and 6, one label from two projects in one build: identity is (block, variant, project),
  and the Configs are distinct since step 15, but the per-label HDL wrapper and registration
  artefacts are named by label alone. A build whose own project does not declare a label that two
  other projects declare is rejected at db time (`validateVariantLabelBuildOwnership`, 2026-09-08)
  rather than emitting one of the two silently. RULED 2026-09-13 (user): owner axis. The bare
  `<block>_<label>` artefacts and the standalone-variant map hold the owner's declarations only;
  every non-owner declaration is served by the qualified top and Config that already exist, the two
  label-keyed view fallbacks and the db rejection go. LANDED 2026-09-13 (plan-parameter-sharing §6
  step 12b, "Label-keyed view fallbacks"); the deviation is closed. The descriptors' `isForeign` keyed on the
  owner of the `ipParameters` context; RULED 2026-09-14 (user): the block's owner (rule 6). A
  definitions-only project may itself declare a variant; it is an ordinary non-owner declaration.
- Rule 6, file ownership when two providers tie: the scanner ranked providers by first-reach depth
  and broke equal-depth ties on path spelling, so a root that lists both a wrapper and the IP the
  wrapper depends on handed the IP's own block file to the wrapper. RULED 2026-09-14 (user): rank
  providers by their longest path from the root (the dependee sits below the dependent and owns the
  shared file); a tie that survives is rejected at scan time naming the file and the providers; a
  `projectFiles:` cycle is rejected. REFINED 2026-09-14 (user) after the full unit suite showed the
  shipped shape (root lists a shared project and its consumers as siblings, the consumers `include:`
  the shared file for scope) ties under longest path: a file listed DIRECTLY in a provider's
  `projectFiles:` belongs to that provider (two direct listings is an error); only unlisted files fall
  to the longest-path rank; the author resolves a rejected tie by listing the file in the owner's
  `projectFiles:`. No directory information anywhere. IN TREE 2026-09-14, gates not yet run: the
  refinement passes the scanner suite and the two shipped shapes it named, but `examples/ip_test`
  still ties on `ip/yaml/ip.yaml` and `ipVariants.yaml` (real-tree `ip` and `ipBridge` both at depth
  one; `ipBridge` reaches the real `ip` project only through its symlink copy, and nobody lists the
  two files directly). RULED 2026-09-14 (user: both resolutions are valid; supervisor's recommendation taken): rule 2
  ranks an edge to a copy of a project as an edge to that project's override-selected master too, so
  the override decides the ranking and ip_test needs no YAML change; rule 1 stays the author's manual
  resolution for unrelated projects. Brief: scratchpad `brief-ownership-override-rank.md`. IN TREE
  2026-09-14: rank edges reach each child's override-selected master, a DFS over the rank edges rejects
  a master-closed cycle (proved to hang `relax()` without it), orphan seeding keys on closure discovery
  rather than depth; 17/17 scanner cells including composed ip_test (`ip.yaml`, `ipVariants.yaml` ->
  ip; `cpu.yaml` -> common) and both standalone roots; `test_eval_sv_emit` 6/6 again. Comments
  trimmed to the four short blocks in `brief-projectscan-comments.md`, scanner suite still 17/17.
  LANDED 2026-09-14, committed in builder/base ab3dc65: unit suite 130/130, base 70/0/4/0, pro 14/0/0,
  product gen/model/VL green.
  (plan-parameter-sharing §6 step 12a, "Ownership tiebreak")
- Rule 9: the layout index collapses cross-project bindings into one slot (item 9B of
  [`plan-116-review-feedback.md`](./plan-116-review-feedback.md)). RULED 2026-09-13 (user): fix now; rows keyed by
  (block, declaring project, variant), the site carrying its declarer from the persisted
  instance-declarer map. LANDED 2026-09-13 (plan-116 9B); the deviation is closed.

### Direction, not a rule

Direction (user, 2026-09-09): SV is the guiding principle. A child binds on its defined ports and
ignores container Config members it does not use. In SC that means payload struct types keyed on
the parameter values they use, with the `<Config>` spelling kept as an alias, so two Configs with
equal values give one type and same-interface thunkers retire. RULED 2026-09-13 (user): opened as a
design step first; the emitted-shape design is written here for review before any generator change,
after the step 15 (c) rename and the step 12a (d) (i) artifact-row view land.

### Design step: value-keyed payload types (written 2026-09-13, for review)

Review 2026-09-14 (user): the shape is understood and looks right; before any generator change, a
hand-edited prototype on a disposable copy of `examples/xprojParam/shared` (the one example that
carries same-interface direct-copy thunkers on one struct, `videoSt`, emitted once in module
`xpGain`) must compile and run with the two thunkers removed, and fail to compile when one Config's
`PIXEL_WIDTH` is changed. Brief: scratchpad `brief-proto-value-keyed.md`. **PROTOTYPE PASSED
2026-09-14**, verified by the supervisor against the copy's diffs and logs (scratchpad
`proto-valuekeyed/`, pristine copy `pristine-valuekeyed/`, `baseline.log`, `proto.log`,
`negative_check.log`). `videoSt` rewritten by hand as `template<uint32_t PIXEL_WIDTH> struct
videoSt_v` plus `template<typename Config> using videoSt = videoSt_v<Config::PIXEL_WIDTH>;` and a
value-keyed `pixel_t_v` alias beside `pixel_t`; the two thunkers, their initialiser entries and the
thunker include deleted from `xpSharedTop.cppm`; each channel bound directly to the child port. The
compiler forced no other edit: no block, base, channel or testbench file changed. Run output matches
the baseline in every data value and both "No error" lines; the only differences are event
ordering, because the retired thunker was a spawned process with its own intermediate channel and
added one handshake stage of latency per hop. Negative check: `PIXEL_WIDTH` 8 to 12 on the filter
Config fails the direct bind with `videoSt_v<8>` against `videoSt_v<12>`; restored, it builds and
runs again. What is lost with the thunker: its intermediate channel's logging, timing and trace
hooks. **RULED 2026-09-14 (user): proceed with the generator implementation.** Decisions taken by the
supervisor for open points 1-3: value-keyed spelling `<name>_v` for structures and types, one template
value parameter per root parameter in the dependency set (sorted, named as the constant, typed as its
Config member); an empty dependency set stays a plain declaration; the cross-interface thunker and its
`directCopy` flag are untouched. The 2026-09-11 inferred-port stopgap is removed; `infPortBad` moves to
unequal values and `infPort` gains a distinct-Config equal-value end. Brief: scratchpad
`brief-valuekeyed-impl.md`. SV byte-identity baseline: scratchpad `sv-before-valuekeyed.sha` (225
files). IN TREE 2026-09-14, under review: emitters value-keyed (`structures.py`, `includes.py`,
`config.py`'s type spelling moved to `intf_gen_utils.configType`), `TYPEPARAMDEPS` persisted beside
`STRUCTUREPARAMDEPS`, `paramTemplateArgs` view, `bindsDirectly` promoted to a method comparing
`_paramValueAtEnd` per root parameter (an inheriting end resolves to a still-generic container value
and binds directly only with another inheriting end), `configTypeIdentity` and the inferred-port
stopgap removed. `xpSharedTop.cppm` lost both thunkers; regenerated `xpGainIncludes.cppm` matches the
prototype. Findings so far: FW headers are value-keyed too (they always carried the Config template);
two UNDECLARED ends with unequal values are not rejected at db (the declared-port payload check never
reaches them), so `infPortBad` currently passes db against its own comment. Supervisor decision: the
stopgap is replaced, not dropped, by a value comparison at the same two `validatePorts` sites, and the
gate reasserts the rejection. Reviewer report 2026-09-14 (eight findings) accepted: undeclared ends
compared through `checkInterfacePair` at the two `validatePorts` skip sites; the `checkAgreement`
downgrade reverted to the generator-bug failure (nothing in the corpus reaches it, and a downgrade would
leave the type and connection flags disagreeing); `paramTemplateArgs` returns constant rows and the
templates spell the C++ type; `_paramValueAtEnd` subscripts the parameter name directly and
`_validateParameterizedConnectionEndpoints` extends to connectionMaps. **Accepted shape:** an inheriting
end against a literal-variant end with equal values keeps its same-interface thunker. The container
class is generic where it is rendered, the render-time view has no per-site values, and the registrar
instantiates a container at every declared variant, not only at connected sites, so equality cannot be
proven from the view; the thunker compiles everywhere. The closing survey classifies such sites as this
accepted class, not as defects. Fix brief: scratchpad `brief-valuekeyed-fixes.md`. Fix round IN TREE
2026-09-14; `_validateParameterizedConnectionEndpoints` then folded its two loop bodies into one
`checkEndpoint` (brief `brief-endpoint-dedup.md`). Post-fix, `test_param_cross_project_linkage.py`'s cell
`test_one_interface_at_differing_configs_is_adapted` failed for the designed reason: its three Configs
all bind WIDTH 8, so the ends bind directly and no producer-end adapter exists. The cell asserted the
retired shape; it is now `test_one_interface_at_equal_valued_configs_binds_directly`: no adapter on
either hop, `bindsDirectly` true for both, and a WIDTH 16 edit on the middle block rejected at db by the
per-field `_bitWidth` check (fault-injected, 10/10; brief `brief-linkage-cell-rework.md`). The same file's
`test_registrar_requirements_exclude_unreachable_child_harnesses` left an empty temp directory per run
since August (156 accumulated); fixed by closing the db before removing the tree (an NFS silly-rename of
the open db file kept the directory), deletion of the leftovers awaits a ruling. Unit suite gate 129/130:
`test_param_type_signedness.py` expected the retired `<Config>` struct for a wide parameterizable type; it
now checks signedness on the `_v` declaration and pins each alias (fault-injected). Base pipeline
70/0/4/0 and pro pipeline 14/0/0 green on the combined tree; every regenerated file is SystemC or C++
(31 `.cppm`, 6 FW `.h` in base; `inhTandem` includes and wrapper in pro) and `sv-compare.sh` proves all
225 SystemVerilog files byte-identical to the pre-change hashes. Seven base containers and the pro
`xpInhWrap` lost every same-interface thunker and bind their ports directly. Product `make gen` clean
(the debayer includes module and FW header regenerate, nothing else beyond the baseline), but the model
build FAILED: `structures.py::constructor` closed its parameter list by replacing the first comma of the
last parameter with `) :`, and `bayer_pixels_per_clock_t_v<BITS_PER_PIXEL_COLOR, PIXELS_PER_CLOCK>` puts a
comma inside the template arguments (`debayerIncludes.cppm:432`, `expected '>'`). No base or pro example
carries a payload sub-type on two root parameters, so the pipelines could not see it; the fix joins the
lists without string replacement and adds a two-parameter cell compiled with clang (brief
`brief-constructor-comma.md`). Fix IN TREE: `constructor` joins parameters and initializers with
`',\n'` and appends the terminator; `test_payload_direct_copy.py` gained
`test_two_param_field_constructor_avoids_comma_splice` (exact emitted line `pixels_st_v<A_W, N> pixels_) :`,
no `) :` inside any template argument list, whole rendered module compiles under `clang++ -fsyntax-only`;
fault-injected against the old code). ip_test and xprojParam/shared regenerate byte-identical. Product
gen, model and Verilator gates rerun green after it (two "No error" each); `sv-compare.sh` still identical.

**Closing survey, 2026-09-14 (scratchpad `thunker-survey.sh`, baseline `thunker-before-valuekeyed.txt`,
result `thunker-after-valuekeyed-final.txt`).** 93 `*_port_thunker<` members before, 62 after, 31 retired
and none added. Retired: every same-interface adapter between two literal-valued Configs with equal
values, in `xprojParam` `cstShared`, `cstUse`, `dpMid` (both wrappers, including the
`dpSt<Config>` against `dpSt<xpDpLeafCustomerConfig<Config>>` pair), `dpTop` (wrapper and tb External),
`inhVar`, `shared`, `twoCtx`, and pro `inhTandem`. The 62 survivors, classified by the two payload types
each adapter names:
- 52 cross-interface (different structure names, the adapter converts representation): `ip_test`
  `ipBridge` (4), `ipStdTop` (1), `ip_top` (2); `simple_ip` (3); `xif` `dutExternal` (2); `xprojParam`
  `cppAxis` (8), `cstBind` (4), `deparam` (4), `mtxElect` (2), `mtxLit` (8), `mtxTpl` (8), `uniq` (4);
  product `tb/debayer/debayerExternal.cppm` lines 60-61 (2). Unchanged from the baseline.
- 8 tb/DUT boundary (`*BoundarySt` against a variant payload): `ip_test/top/model/ip_top.cppm` lines
  67-74. Unchanged.
- 2 accepted container-sourced against literal, same interface: `xif/tb/dut/dutExternal.cppm` lines
  57-58, `streamSt<xif_tbPeerPvSourcedConfig<xif_xif_tbTbV0Config>>` against `streamSt<xif_tbPeerPv0Config>`;
  `pvSourced` takes every parameter by `containerParam:`, so its end resolves to the container token and the
  view cannot prove equality. Same reasoning as the accepted inheriting-vs-literal shape.
- 0 same-interface adapters between two literal-valued ends. No defect.
Ownership rule 6 gates: the same runs cover it (scanner in the unit suite, composed ip_test in both
pipelines). That suite was outside the implementation brief's check list; the
unit-suite gate is what catches such cells, so it runs first. **Closing step (user, 2026-09-14): once the change is gated, survey every
thunker that survives.** After the base, pro and product trees are regenerated, list every
`*_port_thunker<` member in every generated file across the three trees, classify each site by why
it still needs an adapter (different interfaces, tb/DUT boundary, storage-layout difference, or
anything unexpected) and record the classification here with the file and site names. A same-interface
equal-value thunker surviving is a defect in this change.

**The problem.** A parameterizable structure is emitted once as `template<typename Config>
struct dpSt`, and its width expressions read `Config::DP_WIDTH`. Two Configs that resolve to the
same numbers are two C++ types, so a channel typed at one cannot bind a port typed at the other.
Where the child declares `ports:` the generator inserts a same-interface thunker; where the port
is inferred it inserts nothing and the model fails to compile, which the 2026-09-11 db stopgap
now rejects. SystemVerilog has neither problem: a port accepts any same-layout struct, and the
junction check (rule 9) already rejects unequal values.

**The proposal.** Key each payload type on the parameter values it uses, and keep the `<Config>`
spelling as an alias.

- The structure is emitted as a template over the values of the root parameters in its closure,
  which `STRUCTUREPARAMDEPS` already records per structure: `template<uint32_t DP_WIDTH> struct
  dpSt_v`. Width expressions read the template value parameter instead of `Config::DP_WIDTH`.
  A nested parameterizable type or sub-structure is spelled the same way, at the same values.
- The existing name becomes an alias template in the same context module:
  `template<typename Config> using dpSt = dpSt_v<Config::DP_WIDTH>;`. Alias templates are
  transparent, so `dpSt<A>` and `dpSt<B>` are one type whenever `A::DP_WIDTH == B::DP_WIDTH`.
  Every current consumer compiles unchanged: block Base classes and their `using dpSt =
  dpSt<Config>;` lines, channels, testbenches, thunkers, the HDL wrapper boundary.
- `bindsDirectly` compares the resolved values of the payload's parameters at the two sites
  instead of `configTypeIdentity`; the site index resolves those values already. Same interface
  and equal values bind directly, whatever Config each end carries. Same interface and unequal
  values are already a db error. Different interfaces keep today's cross-interface thunker.
- The 2026-09-11 inferred-port stopgap goes: its case is exactly "same interface, equal values".

**What does not change.** Config struct names and contents, the registrar and factory keys,
every SystemVerilog artefact, `_bitWidth` and `_byteWidth`, and the worst-case storage sizing.
The change is confined to the SystemC structure and type emitters and to the bind classification
in the block-data view.

**Open points for the architect.**

1. Spelling of the value-keyed name (`dpSt_v` above is a placeholder) and of the value parameter
   type, which should follow the constant's `valueType`.
2. A structure whose closure has no root parameter dependency but is marked parameterizable
   (`checkAgreement` in `deriveParameterizedDeclSets` reports the disagreement today) stays a
   plain struct.
3. `structureStorageSignature` and the thunker's `directCopy` flag simplify: two sides with equal
   values are one type and never reach the thunker.
4. Proof: the shape from step 13 (an inferred-port child on a distinct Config with equal values,
   `xpRtInhTop` in the register-bus variant) compiles with no thunker; the `infPortBad` fixture
   still rejects at db; every SystemVerilog artefact in the suite byte-identical; model and VL
   runs green across base, pro and the product.

---

## 1. What This Lets You Do

Four authoring situations recur when a parameterizable IP is reused. Each is served by a
different mechanism, and only the last is the subject of this document.

- **A parent block reuses a sub-block's parameter.** The parent needs the same knob its
  child has, because the child's parameterized payload appears on the parent's own boundary.
  The parent names the child's parameter in its own `params:` list, reaching the declaration
  through `include:`. The parameter is still declared once, by the IP that owns it.
- **Several projects share one parameter.** Two projects that must agree on a width name the
  same declaration, again through `include:`. There is one declaration and one identity, so
  the two ends of a connection between them cannot drift apart.
- **Peer blocks share a parameter.** Two blocks that do not contain one another, such as a
  stimulus and a checker either side of an IP, must be configured alike. If they share a
  container, each takes the parameter from that container and agreement is structural. If they
  do not, the assembler declares one plain constant carrying the value and every binding names
  that constant, so the number is written once.
- **A child takes its parameters from the block that contains it.** This is parameter
  inheritance, and it is what the rest of this document specifies. A block is configured by
  the block it sits inside, so a consumer several levels above an IP can configure that IP
  without naming it, and without the IP knowing anything about its consumers.

---

## 2. The YAML

The running example is a three-level design: a leaf IP, a mid-level IP that contains it, and
a customer assembler that contains the mid-level IP and states one value. The leaf is a
debayer, the mid-level IP is an image signal processor, and the customer wants that
processor's debayer configured at a particular algorithm.

| Project | Role |
| :-- | :-- |
| `xpDpLeaf` | leaf IP; owns the parameters `DP_ALGO` and `DP_WIDTH` |
| `xpDpMid` | mid-level IP; contains the leaf, owns its own parameter `MID_ALGO` |
| `xpDpTop` | customer assembler; contains the mid-level IP and states the value |

### 2.1 The IP declares its parameters, names them, and binds its own default variant

```yaml
# xpDpLeaf: the leaf IP. It knows nothing about any consumer.
ipParameters:
    constants:
        DP_ALGO:  { value: 1, maxValue: 7,  desc: "Interpolation algorithm select" }
        DP_WIDTH: { value: 8, maxValue: 32, desc: "Per-instance pixel width" }
    types:
        dpPixelT: { width: DP_WIDTH, maxBitwidth: 32, desc: "Parameterizable pixel word" }

blocks:
    xpDpLeaf:
        desc: "The parameterizable leaf IP"
        params: [DP_ALGO, DP_WIDTH]        # which parameters this block uses
        hasMdl: true
        hasRtl: true
        ports:
            in:  { interface: dpIf, direction: dst }
            out: { interface: dpIf, direction: src }

parameters:
    xpDpLeaf:
        dflt:                              # the IP's own default variant
            DP_ALGO: DP_ALGO               # bound to the constant of the same name,
            DP_WIDTH: DP_WIDTH             # which is how the declared default is written
```

Three facts appear once each. The parameter is **declared** in `ipParameters:`, with its
default in `value:` and the largest value it accepts in `maxValue:`. It is **named** by the
block that uses it, in `params:`. It is **bound** by a variant, which states where an
instance's value comes from.

### 2.2 The container declares its own knob and passes it down

```yaml
# xpDpMid: the mid-level IP. It contains two leaves and passes on whatever it
# was configured at, without stating an algorithm of its own.
include:
    - ../../dpLeaf/yaml/xpDpLeaf.yaml

ipParameters:
    constants:
        MID_ALGO: { value: 2, maxValue: 7, desc: "The algorithm this container asks its leaves for" }

blocks:
    xpDpMid:
        desc: "Mid-level IP containing two leaf instances"
        params: [DP_WIDTH, MID_ALGO]       # DP_WIDTH is the leaf's, reached by include
        hasMdl: true
        hasRtl: true
        ports:
            midIn:  { interface: dpIf, direction: dst }
            midOut: { interface: dpIf, direction: src }

instances:
    uLeafA: { container: xpDpMid, instanceType: xpDpLeaf, instGroup: top, variant: customer }
    uLeafB: { container: xpDpMid, instanceType: xpDpLeaf, instGroup: top, variant: customer }

parameters:
    xpDpLeaf:
        customer:
            DP_ALGO:  { containerParam: MID_ALGO }   # take my container's MID_ALGO
            DP_WIDTH: { containerParam: DP_WIDTH }   # take my container's DP_WIDTH
```

`{ containerParam: NAME }` says: *take this parameter from the parameter called `NAME` on
the block that contains me.* The variant does not name the containing block. The container is
whichever block the instance sits in, which the instance row already states.

Both leaf instances resolve the same container parameter, so the two peers cannot be
configured differently by accident.

### 2.3 The customer states the value once

```yaml
# xpDpTop: the customer. It configures the IP it actually instantiates and never
# names a block two levels down.
include:
    - ../../dpMid/yaml/xpDpMid.yaml

ipParameters:
    constants:
        CUST_ALGO: { value: 3, maxValue: 7, desc: "The customer's own algorithm knob" }

blocks:
    xpDpWrap:
        desc: "Container of the chain; declares the customer knob the mid-level IP inherits"
        params: [CUST_ALGO, DP_WIDTH]

instances:
    uWrap: { container: xpDpTop,  instanceType: xpDpWrap, instGroup: top, variant: customer }
    uMid:  { container: xpDpWrap, instanceType: xpDpMid,  instGroup: top, variant: customer }
    uMid2: { container: xpDpWrap, instanceType: xpDpMid,  instGroup: top, variant: customer2 }

parameters:
    xpDpWrap:
        customer:
            CUST_ALGO: 5                             # the one value the customer states
            DP_WIDTH: DP_WIDTH
    xpDpMid:
        customer:
            DP_WIDTH: DP_WIDTH
            MID_ALGO: { containerParam: CUST_ALGO }  # inherited from xpDpWrap
        customer2:
            DP_WIDTH: DP_WIDTH
            MID_ALGO: 6                              # fixed instead
```

The value travels one level per link: `xpDpWrap.CUST_ALGO = 5` reaches `xpDpMid.MID_ALGO`,
which reaches `xpDpLeaf.DP_ALGO`.

Each level declares the parameter it passes on. The customer writes the number once, on the
one block it owns.

The customer's knob has its own name. The customer file includes `xpDpMid.yaml`, which already
declares `MID_ALGO`, and rule 2 rejects a second visible declaration of that name. (The fixture
`examples/xprojParam/dpTop` spells it `CUST_ALGO`.)

### 2.4 Mixing inherited and fixed parameters

Two kinds of mixture are normal, and both appear above.

**Within one variant.** `xpDpMid.customer` binds `DP_WIDTH` to a value and inherits
`MID_ALGO`. Every parameter of every variant chooses its own form independently.

**Between variants of one block.** `xpDpMid.customer` inherits `MID_ALGO` while
`xpDpMid.customer2` fixes it at `6`. The two variants coexist, and an instance selects
between them with `variant:`.

A container passes on only the parameters it declares itself. `xpDpMid` declares `DP_WIDTH`
and `MID_ALGO` but not `DP_ALGO`, and the leaf's `DP_ALGO` therefore reaches the container's
`MID_ALGO`. A container never becomes a conduit for everything beneath it.

### 2.5 The binding forms

A parameter inside a declared variant may be written in any of these ways, and in no others.

| Written as | Meaning |
| :-- | :-- |
| `PARAM: 5` | the literal value 5 |
| `PARAM: PARAM` | the value of the named constant |
| `PARAM: { value: 5 }` | the literal value 5, long form |
| `PARAM: { containerParam: OTHER }` | taken from the container's parameter `OTHER` |

The short form `PARAM: <scalar>` always means a value, so inheritance is written in the long
mapping form.

---

## 3. What Is Generated

### 3.1 The C++ Config structs

Each declared variant of a block, and the block's default, produces one `Config` whose members
are that block's parameters. Its name carries the project that declares it (rule 5). It takes one of two forms,
and the variant's own bindings decide which:

- **Every parameter bound to a value** produces a plain struct of resolved numbers.
- **Any parameter sourced from the container** produces a struct **template** over the
  container's `Config`. An inherited member reads the named parameter off that `Config`; a
  bound member is still a number.

The leaf IP's own project emits its default and its `dflt` variant. Both bind every
parameter, so both are plain structs:

```cpp
struct xpDpLeaf_xpDpLeafDefaultConfig {
    static constexpr uint32_t DP_ALGO = 1;
    static constexpr uint32_t DP_WIDTH = 8;
};

struct xpDpLeaf_xpDpLeafDfltConfig {
    static constexpr uint32_t DP_ALGO = 1;
    static constexpr uint32_t DP_WIDTH = 8;
};
```

The mid-level IP declares the leaf variant it instantiates, and sources both of its
parameters from itself, so it emits one template:

```cpp
export template<typename ContainerConfig>
struct xpDpMid_xpDpLeafCustomerConfig {
    static constexpr uint32_t DP_ALGO  = ContainerConfig::MID_ALGO;
    static constexpr uint32_t DP_WIDTH = ContainerConfig::DP_WIDTH;
};
```

The customer's project emits one Config per variant it declares, qualified by the project
that declares it, each in whichever form its own bindings call for. `customer` inherits
`MID_ALGO` and is therefore a template; `customer2` fixes it and is a plain struct:

```cpp
export template<typename ContainerConfig>
struct xpDpTop_xpDpMidCustomerConfig {
    static constexpr uint32_t DP_WIDTH = 8;
    static constexpr uint32_t MID_ALGO = ContainerConfig::CUST_ALGO;
};

export struct xpDpTop_xpDpMidCustomer2Config {
    static constexpr uint32_t DP_WIDTH = 8;
    static constexpr uint32_t MID_ALGO = 6;
};
```

A container names its child's Config applied to its own, so the value arrives where the
container is instantiated rather than where the variant is declared:

```cpp
template<typename Config>
class xpDpMid ... {
    std::shared_ptr<xpDpLeafBase<xpDpMid_xpDpLeafCustomerConfig<Config>>> uLeafA;
```

This is the same statement the SystemVerilog makes by forwarding a symbol rather than a
number, and it chains through as many levels as the design has: the leaf inside the
customer's first chain is configured at
`xpDpMid_xpDpLeafCustomerConfig<xpDpTop_xpDpMidCustomerConfig<xpDpTop_xpDpWrapCustomerConfig>>`,
which resolves `DP_ALGO` to the 5 the customer wrote.

A bound value is resolved to a literal. A binding written as `MID_ALGO: MID_ALGO` and one
written as `MID_ALGO: 3` therefore emit the same member; the relationship to the constant is
kept in the authored YAML, not in the emitted struct. An inherited value is not resolved,
because there is nothing to resolve it to until an instantiation states it.

**One Config is emitted per declared variant per block, however many instances select it and
at however many values.** The running example produces two in the leaf IP's own project (its
default and its `dflt` variant), one in the mid-level IP's (the leaf variant that IP
declares), and one per variant the customer declares, in the customer's project. A customer
that adds a third configuration of the mid-level IP adds one Config to its own project and
changes nothing in either IP: the templates the IPs emitted are instantiated at the new
Config, not re-emitted.

Two blocks that resolve to identical numbers still get two distinct Configs, and therefore
two distinct C++ types, with a generated adapter wherever the two meet.

### 3.2 The SystemVerilog

A block's parameters become the module's parameter list, in the order the block names them:

```systemverilog
module xpDpLeaf
import xpDpLeaf_package::*;
#(
    parameter DP_ALGO,
    parameter DP_WIDTH
)
```

A container's parameter list is exactly what that container declares, and an inherited child
parameter is instantiated with the container's own symbol:

```systemverilog
module xpDpMid
#(
    parameter DP_WIDTH,
    parameter MID_ALGO
)
...
xpDpLeaf #(.DP_ALGO(MID_ALGO), .DP_WIDTH(DP_WIDTH)) uLeafA ( ... );
xpDpLeaf #(.DP_ALGO(MID_ALGO), .DP_WIDTH(DP_WIDTH)) uLeafB ( ... );
```

Note that `xpDpMid` declares no `DP_ALGO` at all. The leaf receives the container's
`MID_ALGO`, which is the whole point: the symbol forwarded is the container's, and the names
need not match. A parameter bound to a value rather than inherited appears at the
instantiation as a literal instead of a symbol.

Parameterizable widths follow the same parameters, so a payload declared over `DP_WIDTH`
becomes `typedef logic[DP_WIDTH-1:0] dpPixelT;` inside each module.

---

## 4. Accepted And Rejected Shapes

The rules at the top of this document are normative. This section lists the shapes they accept
and reject and what each message says. A shape marked *not yet enforced* is rejected by the
rules and still accepted by the tree; the deviation list under the rules names the plan step.

### What is allowed

- A parameter is declared once, as an `ipParameters:` constant, in the IP root file or in a
  definitions-only shared file (rule 1). Its `value:` is the default and its `maxValue:` is the
  largest value the IP accepts.
- Any block may **name** that parameter in its own `params:` list, provided it can reach the
  declaration through `include:`. Naming is not declaring, and a block in another project may
  name it.
- A parameter inside a variant may be bound to a value, or sourced from a parameter of the
  block that contains the instance.
- A block's owner may declare a variant labelled `default`. It is then the block's default
  Config, spelled `<project>_<block>DefaultConfig`, and no separate default is emitted for that
  block; its bound values are what the default carries. (Ruled 2026-09-07, from a step 15
  review finding; the product tree declares every variant this way.)
- The child's parameter and the container's parameter need not share a name.
  `DP_ALGO: { containerParam: MID_ALGO }` is an ordinary shape, not a workaround.
- A variant may mix the two forms freely, and a block may declare several variants, some
  inheriting a given parameter and some fixing it.
- One variant may be instantiated under different containers. It means the same thing at
  every site, "take my container's `MID_ALGO`", and each site is checked separately.
- The container's parameter and the child's may be backed by different constants, in
  different projects. They need not be the same declaration.

### What is not allowed

- **A parameter may not be both bound and inherited.** Writing
  `PARAM: { value: 3, containerParam: OTHER }` states the parameter twice. The message names
  the variant and the parameter and says that a parameter is either bound to a value or
  sourced from a container parameter, never both.
- **A parameter may not be left empty.** Writing `PARAM: {}` states nothing. The message says
  that every parameter of a declared variant must be bound or container-sourced.
- **A variant may not omit a parameter its block declares.** There is no default for an
  omitted parameter, and nothing is filled in. The message names the missing parameters and
  lists the ones the block declares.
- **A parameter may not be inherited from a container that does not declare it.** The
  container has nothing to give and, in SystemVerilog, no symbol to forward. The message names
  the instance, the child parameter, the container block, and the parameters that container
  does declare.
- **Inheritance reaches the immediate container only.** A parameter cannot be taken from a
  block two levels up. To configure something deeper, declare the parameter at each
  intervening level and inherit it at each link, as `xpDpMid` does in §2.2. This mirrors
  SystemVerilog, in which a parameter reaches a nested module only through a module that
  declares it.
- **A container parameter may not accept values the child would reject.** If the container's
  parameter is declared with a larger `maxValue` than the child's, it can be bound to a value
  the child cannot accept, and the site is rejected. The message names the instance, both
  constants and both bounds. Declaring the customer's `CUST_ALGO` at `maxValue: 15` in §2.3,
  against a leaf that accepts `7`, is exactly this error.
- **An inherited parameter may not be selected on a top-level instance.** An instance with no
  containing block has no container to inherit from.
- **An instance of a params-declaring block may not select nothing.** The shapes that name a
  Config are the whole list: a variant binding values, a variant sourcing from the container
  per parameter, and `inheritContainerParam: true`. An instance naming none of them leaves the
  block parameterized and the instance untyped, and the two languages then disagree about which
  values it carries. The message names the instance, the block, the block's owning project, the
  file and the line, and lists the parameters the block declares.
- **A top instance's block may not declare `params:` at all.** A top has no container, so
  neither container-sourcing form is reachable, and a project declares one top, so a variant
  could only ever bind one set of literals, which a plain constant expresses without the
  variant machinery. Put an unparameterized block at the root and the parameterized block one
  level down. `examples/xif` is that shape: `xif_top` is the root and the parameterized
  testbench harness `xif_tb` sits inside it at a stated variant. The message states the
  restructure.

- **Two visible declarations of one parameter name** (rule 2), whether the second sits in the
  block's own file or in another included file. The message names every declaring file.
- **A variant label with zero or two visible declarations** (rule 7). The message names every
  declaring file it can see, or the file(s) that declare it out of scope.
- **An instance of a block without `params:` names a variant.** No file could ever declare a
  variant of it, so the message says the block declares no params rather than that no file
  declares the label.
- **`inheritContainerParam:` across a project boundary** (rule 4). The message names both
  projects. A cross-project child takes a declared variant whose bindings are `containerParam:`.
- **A register-bus interface carrying a parameterizable structure** (ruled 2026-09-11). An
  interface whose type is `addressBus: true` is fixed-width on every side of every router. A
  register or memory behind the bus may be sized by a parameter, because address allocation
  scopes it at its maximum; the bus structure itself may not, because no master, dispatch or
  boundary can be typed to drive it. The message names the interface, its type, the
  parameterizable structures and the file, and says to move the parameter onto the payload.
- **A `hasRtl: true` container with no `params:` assembling a channel over a parameterizable
  interface** (ruled 2026-09-11). The SystemVerilog package emits no typedef for a
  parameterizable structure and a block without `params:` declares none locally, so the
  container's module would instantiate the channel with a type that exists nowhere. A
  model-only container keeps the transit shape. This is an emitter gap held as a rejection, not
  a rule of the design: rule 4 makes the shape legal, and a resolved-literal local typedef in the
  container module would lift it. The message names the container, the channel,
  the interface, both ends and the file, and offers three fixes: declare `params:` on the
  container and inherit or bind the children, make the structure fixed-width, or set
  `hasRtl: false`.
- **A `registerPorts:` key that differs from the nested router's `upstreamPort`** (ruled
  2026-09-11). The synthesised boundary map wires the container's declared port straight
  through to the router's upstream port by name, so the two names are one port. The message
  names the container, its key, the router and its upstream port.

Where one variant is reused under several containers, the same rules apply once per site.
Two containers backed by the same constant, and two backed by different constants with the
same `maxValue`, are both accepted; only a container whose accepted range exceeds the child's
is rejected, and only at the site where that happens.

- **An undeclared port of a params-declaring block binding a channel whose parameter values
  differ** (ruled 2026-09-11 as a Config-identity stopgap; superseded 2026-09-14 by value-keyed
  payload types). A port the block does not declare in `ports:` is inferred top-down and binds the
  channel directly. Payload types are keyed on the parameter values they use, so equal values are
  one C++ type and bind with no adapter whatever Config each end resolves at. `make db` rejects the
  bind only when a value the payload uses differs between the two ends, naming the block, the
  instance, the port and the differing values. Fixtures: `examples/xprojParam/infPort` (equal
  values at distinct Configs, accepts) and `infPortBad` (differing values, rejects).

### What is not checked

`maxValue` is the whole of the compatibility relation. It bounds the magnitude the container
may bind and says nothing about the value's **type**, so **`valueType` is not compared**: a
signed container parameter sourced into an unsigned child parameter is accepted, and the
child's Config member is emitted at the child's own declared type. Extending the relation to
`valueType` was raised and **declined**. The failure needs a signed container parameter bound
into an unsigned child, which was judged too narrow to widen the relation for. It is a known
and accepted gap, so there is no diagnostic to wait for.

Keeping the container's and the child's `valueType` in agreement is therefore the author's
responsibility, not the generator's.

---

## 5. What Is Supported Today

All four situations in §1 are available and in use, including the shared declaration of rule 1,
a definitions-only file declaring a parameter for several IPs (`examples/xprojParam/cstShared`).
For parameter inheritance, the fourth and the subject of this document, that means:

- The authored YAML of §2 is accepted, and every shape in §4 not marked *not yet enforced* is
  rejected with the message described there.
- The SystemVerilog of §3.2 is complete: parameters are forwarded through each level and the
  design elaborates and runs with the inherited values.
- The C++ of §3.1 is complete: a customer's value reaches a leaf two project levels down, and
  two containers of one IP at different values resolve independently at run time.
- An inherited parameter that appears in a **width** is inside the interface layout comparison,
  resolved at the value the site actually binds.
- All of the above is held by automated targets rather than by recorded runs.

A router serves one bus type, named by its `addressBlock.upstreamPort`, on both of its sides.
A router block may declare `params:` and inherit or take `containerParam:` values like any
block, and the junction between a parent router and a nested router is adjudicated at the
configuration that governs both, the same as every other connection. The bus itself is
fixed-width by rule (§4): since 2026-09-11 a parameterizable structure on an address-bus
interface is rejected at `make db`, so the parameter goes in the register payload, as
`examples/xprojParam/rtInh` does with its leaf's `cfg` register.

One thing is not covered, and an author has to know it:

- **`valueType` is not compared** between the container's parameter and the child's; see
  "What is not checked" in §4.

A second item stood here until 2026-09-14: that a top-down port at a Config other than the
channel's was rejected rather than bound. Payload types are now keyed on parameter values (the
design step under "Direction, not a rule"), so equal values bind directly and only a differing
value is rejected (§4).

A third item stood here until 2026-09-07: that a block's Config could carry parameters
declared in the same file that the block does not name. Since 2026-09-05 a block's Config
carries exactly the parameters its `params:` list names, and derived constants are computed in
the implementation ([`plan-parameter-sharing.md`](./plan-parameter-sharing.md) §6, step 3).
A block that names parameters from two files gets one Config name and one home whatever its
`params:` order: every Config name carries the declaring project, and each (declaring project,
block) emits one module (rule 5, plan step 15, landed 2026-09-07).

The status, the remaining work and the evidence behind each claim are tracked at
[`plan-parameter-sharing.md`](./plan-parameter-sharing.md) §6, step 7, which also carries the
history of what this document used to say.

`inheritContainerParam:` stays supported as rule 4's same-project, same-name shorthand, and the
synthesised register handler keeps using it. The product tree's `u_preprocess`/`u_interpolate` use
`inheritContainerParam:`; the `containerParam:` form remains for a child that differs from its
container by name or project.
