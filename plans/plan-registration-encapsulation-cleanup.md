# Plan: Registration Encapsulation Cleanup (force_link follow-up)

## Status

- **Direction:** **decided — Option δ** (compiler retain attribute +
  build-system contract). `α` held as fallback, not needed. `β` / `γ`
  not pursued. Decision recorded 2026-06-23 in
  [`research-block-registration-options.md`](./research-block-registration-options.md)
  ("Decision Addendum (2026-06-23): `force_link` retirement — Option δ
  selected").
- **Status taxonomy (reconciled 2026-07-24):** complete and committed. The
  generator/prototype/example changes are in branch history and `force_link`
  remains retired.
- **Current decision state:** W7 (δ matrix) and W2 (tandem proto) pass
  on clang 20 + gcc 13; W5 δ-branch generator edits landed; all eight
  `examples/*` regenerate with zero `force_link` and build/run; W6 docs
  updated.
- **Next action:** none. The old optional live-`debayer`/WI6 note is historical;
  WI6 was subsequently closed/descoped.
- **Parent plan:**
  [`plan-block-registration.md`](./plan-block-registration.md) — owns
  the Force-Link Function design as it stands today. This plan is the
  follow-up that revisits the encapsulation cost of that design and
  closes verilator / tandem coverage gaps the original Stage 0
  prototype did not exercise.
- **Touches:**
  [`plan-variant-config-unification.md`](./plan-variant-config-unification.md)
  Stage 4.4 / Stage 9.3 — those stages established the per-block
  trampoline pattern for parameterized SC blocks. This plan asks
  whether the same pattern should subsume the non-templated path.

## Problem Statement

The instance-factory design relies on string-keyed lookup so that a
parent container only needs the child's *type name* and *variant*
string to create the child. The factory closes over the child's
`make_shared<...>(...)` inside a registered lambda; the parent never
references the child class. That indirection is the encapsulation
contract — the parent's translation unit (TU) has no compile-time
symbol dependency on the child's implementation TU.

Stage 0 of the block-registration work uncovered a linker problem
under C++20 modules and static-archive linking: a child's
self-registering static lives inside the child's own `.cpp`, but the
parent does not name a symbol from that `.cpp`, so the linker is free
to elide the entire object and the registration never fires. The
Stage 0 prototype validated an active `force_link_<block>()` function:
a no-op function defined in the child's `.cpp` whose declaration the
parent calls, creating a real link-time reference that forces the
archive member in.

The price: every parent constructor and every testbench now carries
a compile-time symbol reference to every non-templated child it
constructs. The factory's encapsulation contract is intact at the
**lookup** call site (still a string key) but broken at the
**linkage** layer (parent now knows the child by symbol name).

Concretely, `examples/mixed/model/mixed.cpp` after Stage 4.4 / 9.3
emits:

```cpp
mixed::mixed(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("mixed", name(), bbMode)
        ,mixedBase(name(), variant)
        ,...
        ,uBlockA(std::dynamic_pointer_cast<blockABase>((force_link_blockA(),    instanceFactory::createInstance(name(), "uBlockA",   "blockA",    ""))))
        ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>((force_link_apbDecode(), instanceFactory::createInstance(name(), "uAPBDecode","apbDecode", ""))))
        ,uBlockC(std::dynamic_pointer_cast<blockCBase>((force_link_blockC(),    instanceFactory::createInstance(name(), "uBlockC",   "blockC",    ""))))
        ,uBlockB(std::dynamic_pointer_cast<blockBBase>((force_link_blockB(),    instanceFactory::createInstance(name(), "uBlockB",   "blockB",    ""))))
```

The comma-operator squeeze is an implementation pragmatic, not a
documented design choice — `plan-block-registration.md:458-464`
prescribes two sequential statements, but the existing constructor
template binds children as mem-initialisers and the implementation
chose to keep the mem-init list intact at the cost of readability.
Worse, the parent now *imports* — at the linker level — every
non-templated child it touches.

## Current State by Block Category

| Category | Registration lambda lives in | Reachable because… | `force_link` emitted? |
|---|---|---|---|
| Templated SC block | `<block>Registrar.cpp` trampoline TU | trampoline TU listed by project Makefile, unconditionally linked | NO |
| Non-templated SC block | self-registering static in `<block>.cpp` | `<block>.cpp` may be elided under modules / static archive | **YES** — `force_link_<block>()` in every parent and in the testbench's DUT mem-init |
| Verilator wrapper | template-specialised `registerBlock_` static in `<block>_hdl_sc_wrapper.h`, instantiated by explicit specialisation in `vl_wrap.cpp` | `vl_wrap.cpp` is the per-project verilator aggregator TU, unconditionally linked | NO |
| Tandem `_verif` side | same as verilator wrapper | same as verilator wrapper | NO |
| Tandem `_model` side (non-templated) | same as non-templated SC block | same as non-templated SC block | inherits — **never validated end-to-end** |
| Tandem `_model` side (templated) | same as templated SC block | same as templated SC block | NO |
| Testbench top | self-registering static in `<block>Testbench.cpp` | testbench TU may be elided | **YES** — `force_link_<B>Testbench()` from `main` (`templates/systemc/testbench.py:316,345`); the DUT mem-init also carries a `force_link_<B>()` for the non-templated DUT case (`templates/systemc/testbench.py:362`) |

The pattern: `force_link` is required exactly where the registration
lambda lives in a TU the project build does not unconditionally
reference. The trampoline / aggregator approach (templated SC,
verilator) does not need it because the trampoline TU is named by the
project Makefile, and the trampoline owns the symbol reference into
the block's class definition.

## Why this weakens the encapsulation

For templated blocks the asymmetry does not exist because the
trampoline already provides the named anchor: the trampoline is the
one place that knows the block's class, the project Makefile lists
the trampoline, the linker pulls the trampoline in, the trampoline's
static initialiser runs, and the lambda it registers closes over
`make_shared<B<Config>>`. Parents only ever see `<child>Base.h`.

For non-templated blocks the registration lives in the block's own
`.cpp`. The project Makefile does list that `.cpp`, but under modules
the **linker is allowed to drop the resulting object** if no symbol
from it is referenced. The factory's string-keyed lookup does not
count as a symbol reference. Hence `force_link`.

`force_link` works around the linkage problem but undoes the
encapsulation property: the parent's `.cpp` (and the testbench's
`.cpp`) now carries `force_link_blockA`, `force_link_apbDecode`,
`force_link_blockC`, `force_link_blockB` symbol references. Each
parent's compilation now fails if a child is renamed or removed
without the parent regenerating — which the generator handles in
practice, but the *property* the factory was meant to provide is
gone for the non-templated half of blocks.

## Verilator / Tandem coverage status

- **Verilator wrappers (today).** Use the `vl_wrap.cpp` aggregator,
  which plays the trampoline role. Each `<block>_<variant>_hdl_sc_wrapper::registerBlock_`
  is explicit-specialised once in `vl_wrap.cpp`. `vl_wrap.cpp` is
  unconditionally linked by the verilator-enabled build target. No
  force_link involved. **Works.**
- **Tandem `_verif` side.** Inherits the verilator path. **Works.**
- **Tandem `_model` side, parameterized.** Inherits the templated SC
  trampoline path. **Works.**
- **Tandem `_model` side, non-templated.** Inherits the non-templated
  SC path. The tandem wrapper is the parent that calls
  `createInstance(..., "_model")`. `templates/systemc/constructor.py`'s
  `if not instIsParameterizable` branch emits `force_link_<model_block>()`
  there. **Code path exists but the Stage 0 prototype never exercised
  tandem.** A real tandem-with-non-templated-model build has not been
  end-to-end verified.

The Stage 0 prototype (`proto/model/test/test_block_registration.cpp`)
proves:

- A non-templated block in a static archive registers correctly when
  the test binary calls `force_link_<block>()` (this is the
  `apbDecode` case).
- A templated block in a static archive registers correctly when its
  trampoline TU is in the same archive (this is the `ip` case via
  Option 9 in the research doc).
- A verilated wrapper registers via explicit specialisation.

The prototype does **not** prove:

- Whether a non-templated block in a static archive could register
  correctly if its registration were moved out of `<block>.cpp` into
  a separate `<block>Registrar.cpp` listed by the project Makefile —
  i.e., the "α" option below.
- Whether tandem wraps the lookup correctly for a non-templated model
  child end-to-end.
- Whether a project-level aggregator TU (like `vl_wrap.cpp`) extended
  to cover SC blocks resolves the registrations correctly under
  modules — i.e., the "β" option below.

## Options

These are not "tweak the emission" — they restructure where the
registration lambda lives. Each carries different costs.

### Option α — Trampoline for every SC block

Broaden the `blockRegistrar` `fileMap` entry from
`cond: {isParameterizable: true, hasMdl: true}` to
`cond: {hasMdl: true}`. Every SC model block, templated or not, gets a
`<block>Registrar.cpp` that owns the registration lambda. The block's
own `.cpp` no longer carries the self-registering static. The
trampoline is the only TU that names the block class.

Consequence:

- `force_link_<block>()` calls disappear from every parent and from
  the testbench. The mem-init list returns to clean
  `dynamic_pointer_cast(createInstance(...))`.
- The same code shape covers templated and non-templated alike —
  symmetric, uniform.
- The block's `.cpp` becomes lookup-target-agnostic: its symbols are
  referenced only by the trampoline. Removing or renaming a child no
  longer touches the parent's `.cpp` at the symbol level (only at the
  generator-emitted string-key level).

Cost:

- One additional generated TU per non-templated SC block. Tiny
  (one lambda + one static initialiser). Identical structure to the
  existing parameterized-block trampoline.
- Stage 0-style proto needed to confirm: a non-templated block
  packaged in a static archive plus a separate
  `<block>Registrar.cpp` (also in the archive) registers via the
  trampoline's static initialiser when the project Makefile lists
  only the trampoline.
- `force_link` machinery for SC blocks (declaration in `<block>Base.h`,
  definition in `<block>.cpp`, generated call sites) can retire.
- Testbench top (`<B>Testbench.cpp`) is a parallel case: a
  `<B>TestbenchRegistrar.cpp` would close that gap too.

### Option β — Project-level aggregator TU

Single `<project>_registrations.cpp` lists every
`instanceFactory::registerBlock(...)` for the project, mirroring how
`vl_wrap.cpp` aggregates verilator registrations. Block `.cpp` and
`<block>Registrar.cpp` both retire. The aggregator is the only TU
naming any block class.

Consequence:

- Same encapsulation win: no parent ever references a child symbol.
- One TU per project instead of one per block.
- Closer to research doc Options 2A / 2C / 4.

Cost:

- The aggregator changes whenever the project's block list changes
  (less text-stable than per-block trampolines).
- The aggregator `#include`s / `import`s every block's class
  definition (potentially heavy compile in one TU).
- Diverges from the templated-block convention (which is per-block).
- Symmetric only if we also retire `<block>Registrar.cpp` for
  templated blocks, which is a regression on Stage 9.2 / 9.3 work.

### Option δ — Compiler attributes + build-system policy

Leave the registration as a self-registering static inside the
block's own `.cpp`, but mark the static with
`__attribute__((used, retain))` (with portable fallbacks for older
compilers / MSVC). Document that any project packaging SC blocks
as static archives must apply `-Wl,--whole-archive` (or the
platform equivalent — `/WHOLEARCHIVE:` on MSVC, `-force_load` on
Apple ld64) to those archives. Direct-`.o` linking — the current
shape of every project Makefile in `examples/` — needs no
additional build-system flag.

`force_link_<block>()` declarations, definitions, and call-site
emissions retire entirely. The factory's encapsulation contract is
restored at the source level: parents and the testbench have **zero**
compile-time symbol references to non-templated children.

#### Why this works

The current production builds for `examples/ip_test` and
`examples/mixed` list every block `.o` individually on the link
command, not through an archive. Archive-elision is not a concrete
problem in today's builds — the archive case the Stage 0 prototype
exercised is preventive against a future build configuration.
For direct-`.o` linking, the registration static fires
unconditionally; `__attribute__((used, retain))` only needs to
protect it from `--gc-sections` and from compiler-side dead-code
elimination, both of which the attribute pair handles portably on
GCC and Clang.

For archive-packaged builds, no source-level pragma can override the
linker's archive-extraction rule (no symbol reference → no
extraction), so the project's build system must use
`--whole-archive` or an equivalent. This makes the build-system
contract explicit rather than papering over it with per-call-site
force-link references.

Consequence:

- No new TUs (α adds one per block; β adds one per project).
- No mem-init ugliness (γ is purely cosmetic).
- Encapsulation contract restored at the source layer.
- Build-system contract becomes load-bearing — a project shipping
  blocks as archives must use `--whole-archive` or an equivalent
  on those archives. Documentation requirement, not generator
  requirement.

Cost:

- A project that adopts archive packaging without `--whole-archive`
  will silently lose registrations. Mitigated by a build-system
  policy doc and by the proto matrix below.
- MSVC compatibility requires a portability shim around
  `[[gnu::used]] [[gnu::retain]]`. The same shim already exists in
  several SystemC-adjacent codebases.
- Slightly different attribute support across compiler versions;
  the proto must confirm the attribute pair behaves as expected on
  the build's target toolchains (clang 14+, gcc 11+).

### Option γ — Hide the ugliness only

Leave `force_link` as the linkage mechanism but emit it as a
namespace-scope static in the parent's `.cpp` (function-pointer
take-address) instead of comma-operator in the mem-init:

```cpp
namespace {
[[maybe_unused]] auto _link_mixed_blockA    = &force_link_blockA;
[[maybe_unused]] auto _link_mixed_blockB    = &force_link_blockB;
[[maybe_unused]] auto _link_mixed_blockC    = &force_link_blockC;
[[maybe_unused]] auto _link_mixed_apbDecode = &force_link_apbDecode;
} // namespace
```

The mem-init list reverts to clean
`dynamic_pointer_cast(createInstance(...))`.

Consequence:

- Mem-init reads cleanly.
- One block of anchors per parent, regardless of child count.

Cost:

- The architectural problem — parent has compile-time symbol
  references to every non-templated child — remains; this is
  cosmetic only.
- Needs proto validation that a function-pointer take-address creates
  the same link-time relocation a direct call does. The Stage 0
  prototype tested the call form, not the take-address form. Modern
  toolchains should treat them equivalently for static-archive
  member extraction, but the research doc was explicit that the
  passive inline-variable form is unreliable; take-address sits
  between those two extremes and deserves a focused proto.

## Recommendation

δ is the most attractive option *if* the proto matrix in W7
validates and the project is willing to make `--whole-archive` (or
direct-`.o` linking) an explicit build-system contract. Reasons:

- Smallest footprint — no new TUs, no generator changes beyond
  retiring `force_link` emission and adding the attribute pair.
- Restores the source-level encapsulation contract completely:
  parents and testbench have zero compile-time references to
  non-templated children.
- Current production builds already satisfy δ's runtime
  prerequisite (direct-`.o` linking) without any build change.
- Tandem and verilator paths gain nothing extra from δ — verilator
  already routes through `vl_wrap.cpp`'s aggregator, and tandem
  inherits whichever underlying mechanism is in use.

α is the fallback if δ does not validate (e.g., if the attribute
pair does not protect against the relevant linker passes on the
build's target toolchains, or if the build-system contract is
deemed too implicit). α reuses the trampoline shape already proven
for templated SC and available in
`templates/systemc/blockRegistrar.py`. The trade-off: one extra TU
per non-templated SC block.

β is preferable only if the project Makefile would otherwise have to
track per-block trampoline files individually — which it already does
for templated blocks today, so β does not save any Makefile pain.

γ is acceptable as a short-term cosmetic improvement if δ / α / β
are all deferred, but does not address the underlying issue and
should not be treated as a steady-state design.

## Work Items

### W1 — Proto: α-style trampoline for a non-templated block in an archive

Update `proto/model/test/` to add a variant of the existing
`apbDecode` case in which the `instanceFactory::registerBlock(...)`
call is moved out of the block's `.cpp` into a new
`apbDecodeRegistrar.cpp`. Package both `.cpp` files in the existing
static archive. The test binary calls only `createInstance(...)` — no
`force_link` references anywhere. Confirm:

- The registrar TU's static initialiser fires.
- `createInstance("apbDecode", ...)` succeeds.
- The original block's `.cpp` is still archived (it carries the
  class definition `apbDecode::apbDecode(...)` etc. that the
  registrar's lambda calls into via `make_shared`).
- Linker behaviour is consistent across clang and gcc.

If yes, α is mechanically viable. Promote to a plan stage.

### W2 — Proto: tandem coverage with non-templated _model child

The existing prototype does not exercise tandem. Extend the proto
with:

- A tandem wrapper instance that names a non-templated `_model` and
  a verilated `_verif`.
- The tandem wrapper packaged in the static archive.
- The test binary creates the tandem instance via
  `instanceFactory::createInstance(...)` only.

Confirm both sides register and resolve. Document any additional
force-link emission the tandem wrapper requires under the current
mechanism. If α lands first, repeat this proto under α and confirm
no force-link calls are needed.

### W3 — Proto: testbench force-link parallel case

`templates/systemc/testbench.py` emits a `force_link_<B>Testbench()`
function for the testbench top. This has the same architectural
shape as the parent / child case — the testbench TU may be elided
under modules unless `main` calls a function from it. Under α this
would be retired by emitting a `<B>TestbenchRegistrar.cpp`. Confirm
the proto covers the testbench case end-to-end, or extend it.

### W7 — Proto: δ attribute matrix and direct-`.o` vs archive linking

Validate Option δ across the build configurations that matter:

1. **Direct-`.o` linking, no `force_link`**, with the registration
   static carrying `__attribute__((used, retain))`. Confirm the
   self-registering static fires and `createInstance(...)` succeeds.
   This mirrors today's production build.
2. **Static archive, no `force_link`, no linker flag**, with
   `__attribute__((used, retain))` on the registration static.
   Expected to **fail** — proves that the build-system contract is
   load-bearing.
3. **Static archive, no `force_link`, with `-Wl,--whole-archive`**
   wrapping the block archive, attribute pair present. Confirm
   registration fires.
4. **Static archive, no `force_link`, with `-Wl,-u <reg_symbol>`**
   adding an undefined-symbol reference, attribute pair present.
   Confirm registration fires. (Equivalent of an explicit
   per-archive force-link without the source-level call.)
5. **Modules-mode build, direct-`.o` linking, no `force_link`**,
   attribute pair present. Confirm registration fires under the same
   modules flags `examples/ip_test` already uses
   (`-fmodule-file=...`, `--precompile`, etc.).
6. **Compiler matrix**: clang 14+ and gcc 11+. Both must honour
   `[[gnu::used]] [[gnu::retain]]` semantics on a static variable
   at namespace scope and within an anonymous namespace.

Record the outcomes in
`research-block-registration-options.md` as a new dated decision
entry. If 1, 3, 4, 5 all pass and 2 fails as expected, δ is
mechanically sound. If any of 1 / 3 / 4 / 5 unexpectedly fails,
either α becomes the recommendation or a per-toolchain
workaround is needed (e.g., dropping `retain` and relying on
`used` plus `-Wl,--no-gc-sections`).

The proto should reuse the existing `apbDecode` non-templated
case in `proto/model/test/`. Tandem-with-non-templated-model (W2)
can be folded into this matrix to confirm tandem inherits δ's
behaviour transitively.

### W4 — Option γ proto (only if α and β are deferred)

Validate that `&force_link_<block>` as a namespace-scope static
initialiser in the parent's `.cpp` creates the same archive-member
extraction as a direct call. Test in both clang and gcc with
modules and static-archive linkage. If yes, γ is a drop-in cosmetic
fix to `templates/systemc/constructor.py` and
`templates/systemc/testbench.py`.

### W5 — Generator changes (α or δ path)

#### α path — conditional on W1 passing:

- `config/project.yaml` `fileMap['blockRegistrar']`: broaden `cond`
  to `{hasMdl: true}` (drop the `isParameterizable: true` filter
  unless the file-map needs to remain templated-specific for some
  other reason — confirm by reading `pysrc/newModule.py`'s
  `getBlockConfigView` consumer).
- `templates/systemc/blockRegistrar.py`: ensure the trampoline
  renders correctly for non-templated blocks
  (`hasOwnParams == False`). The existing template already has the
  non-leaf-parameterizable case for containers; the non-templated
  case should require minimal additional logic — registration lambda
  uses `make_shared<B>(...)` (no `<Config>`).
- `templates/systemc/constructor.py`: drop the
  `if not instIsParameterizable: createCall = f'(force_link_..., ...)'`
  branch. Drop the `force_link_<className>` definition emission in
  `blockRegistrarInitLines`.
- `templates/systemc/baseClassDecl.py` (or wherever the
  `force_link_<block>` declaration is currently emitted in
  `<block>Base.h`): drop that emission.
- `templates/systemc/testbench.py`: drop the
  `force_link_<B>()` and `force_link_<B>Testbench()` emissions; add
  a `<B>TestbenchRegistrar.cpp` companion (or use the same
  blockRegistrar mechanism for testbench blocks if the cond predicate
  matches).
- Audit every consumer of `force_link_<block>` and confirm there are
  no remaining call sites.

#### δ path — conditional on W7 passing:

- Introduce a portable `A2C_REGISTRATION_RETAIN` macro (or similar)
  in `common/systemc/instanceFactory.h` that expands to
  `[[gnu::used, gnu::retain]]` on GCC/Clang, `__declspec(selectany)`
  or equivalent on MSVC, and nothing on toolchains that need a
  build-system-only solution.
- `templates/systemc/constructor.py::blockRegistrarInitLines`:
  apply `A2C_REGISTRATION_RETAIN` to the `_<className>_registered`
  static initialiser variable.
- `templates/systemc/constructor.py`: drop the
  `if not instIsParameterizable: createCall = f'(force_link_..., ...)'`
  branch and drop the `force_link_<className>` definition emission.
- `templates/systemc/baseClassDecl.py`: drop the
  `force_link_<block>` declaration emission.
- `templates/systemc/testbench.py`: drop the `force_link_<B>()`
  and `force_link_<B>Testbench()` emissions; apply
  `A2C_REGISTRATION_RETAIN` to the testbench's own registration
  static.
- `templates/systemc/blockRegistrar.py`: apply
  `A2C_REGISTRATION_RETAIN` to the trampoline's registrar instance
  for symmetry, even though it is not strictly required (the
  trampoline TU is unconditionally linked today).
- Audit every consumer of `force_link_<block>` and confirm there are
  no remaining call sites.
- Add a build-system policy doc (or section in
  `plan-development-ordering.md`) that records the
  `--whole-archive` contract for projects packaging SC blocks as
  archives.

### W6 — Documentation cleanup (α or δ path)

- `plan-block-registration.md` "Force-Link Function" section
  becomes historical; replace with a short subsection that points
  to this plan and to the retirement commit.
- `research-block-registration-options.md` Option 6a / Open Question
  11 entries gain a "retired in favour of universal trampoline" cross-
  reference.
- `plan-variant-config-unification.md` Stage 4.4 / 9.3 entries note
  that the `force_link_<block>` calls those stages preserved are
  now retired.

## Execution Record (2026-06-23)

Option δ selected and implemented. Summary (full proto table and
build-system contract in the research doc's 2026-06-23 addendum):

- **W7 (δ matrix) — done.** `proto/model/test/delta_matrix.sh` on
  clang 20.1.8 + gcc 13.1.0. Direct-`.o` (D1a/b/c) PASS, archive-no-flag
  (D2) FAIL as expected, `--whole-archive` (D3) and `-Wl,-u` (D4) PASS,
  modules (D5) PASS. Finding: direct-`.o` is a GC root so registration
  survives even without `retain`; the build-system contract is
  load-bearing only for archive packaging.
- **W2 (tandem proto) — done.** Added `block_registration_delta_tandem.*`
  + `test_block_registration_delta_tandem.cpp`: a `<block>Tandem`
  wrapper builds `_verif` (registrar static) and the non-templated
  `_model` (δ static) through the factory only, no `force_link`. PASS on
  direct-`.o` (T1, clang+gcc) and modules (T2, clang). Closes the
  tandem-non-templated-`_model` gap the Stage 0 prototype never
  exercised.
- **W5 (δ generator branch) — done.** `A2C_REGISTRATION_RETAIN` added to
  `common/systemc/instanceFactory.h`; `force_link` emission removed and
  the attribute applied in `templates/systemc/constructor.py`,
  `baseClassDecl.py`, `testbench.py`, `blockRegs.py`, and
  `templates/fileGen/fileGen.py`. All eight `examples/*` regenerate with
  zero `force_link` and build/run without regression. User-owned
  `*Config.cpp` skeletons that carried hand-migrated `force_link` calls
  were cleaned.
- **W6 (docs) — done.** Research-doc decision addendum added; Option 6a
  and Open Question 11 marked retired/resolved; this plan's Status
  updated; build-system contract recorded in the addendum.
- **W1 (α proto) / W3 (testbench α) / W4 (γ proto) — not needed.** α was
  the fallback; δ validated, so the α/γ protos were not built.

Note on `debayer`: regenerating it also produces zero `force_link`, but
a live tandem run is blocked by the unrelated in-progress `yamlFormat: 2`
/cppm migration (base headers emit `import shared_types;` with no
generated `.cppm`), which fails the first compiled TU independently of δ.
Tandem coverage for δ is provided by the proto (T1/T2).

## Open Questions

- **Q1.** Does a function-pointer take-address (`&force_link_<block>`)
  in a namespace-scope static initialiser in the parent's `.cpp`
  create a link-time reference strong enough to extract a static-
  archive member? If yes, γ is a viable interim. If no, γ is
  unsound. (W4)
- **Q2.** Under modules-mode, is there any block category where
  α breaks down — e.g., a block whose registration lambda needs
  template-context state that only the block's own TU has visible?
  The templated trampoline already solves this by `#include`-ing
  `<block>.h` to instantiate, so the answer is likely no, but worth
  a focused review during W5. (review)
- **Q3.** If α retires the in-block self-registering static, does any
  test or scaffold depend on the block self-registering when the
  trampoline TU is *not* linked (e.g., a unit test that pulls in
  `<block>.cpp` directly without the project Makefile's trampoline)?
  Most likely no, since the proto already requires the trampoline
  TU for templated cases, but worth a `grep` of unit-test scaffolds.
  (review)
- **Q4.** Tandem block ergonomics under α: the tandem wrapper's
  constructor builds both sides via `createInstance(..., "_model")`
  and `createInstance(..., "_verif")`. Under α both lookups resolve
  through trampolines (the SC trampoline and `vl_wrap.cpp`
  respectively). Should the tandem wrapper itself live in a per-
  block trampoline or in the project's testbench trampoline? Open.
  (W2)
- **Q5.** Does the project commit to direct-`.o` linking for the
  foreseeable future, or does it anticipate shipping SC blocks as
  static archives / consumable libraries? δ's viability hinges on
  this answer. Direct-`.o` is the current state of every Makefile
  in `examples/`; if the answer is "always direct-`.o`", δ's
  build-system contract collapses to "no extra flags required" and
  the attribute pair is the only thing needed. (project-level
  decision, not a proto question)
- **Q6.** Compiler portability of `[[gnu::used, gnu::retain]]`: do
  the build's target toolchains include any compiler where this
  attribute pair is unavailable or has different semantics?
  Specifically: which gcc / clang minimums does the project
  support, and is MSVC ever a target? δ's portability shim depends
  on this. (W7)

## Relation to Other Plans

- **`plan-block-registration.md`** — owns the Force-Link Function
  design as currently implemented. This plan is the successor when
  α (or β) lands.
- **`plan-variant-config-unification.md`** — Stages 4.4 / 9.3 made
  the encapsulation gap visible by completing the per-block
  trampoline path for parameterized SC blocks while leaving the
  non-templated path on force_link. No work in those stages is
  affected by this plan; they remain correct against the design as
  written.
- **`research-block-registration-options.md`** — Option 6a (passive
  anchor) and the Stage 0 prototype's promotion to the active force-
  link function are recorded there. The encapsulation cost of the
  active force-link function was not surfaced as a primary criterion
  at the time of the 2026-05-05 decision; this plan revisits that
  cost in light of concrete generated output.
- **`plan-development-ordering.md`** — the broader cppm migration
  ordering plan. α / β decisions should slot into a checkpoint here
  once W1 / W2 land.

## Out of Scope

- The cppm migration of `examples/mixed` is owned by M1 / M3 in
  `plan-development-ordering.md` and is independent of this plan.
- Verilator-wrapper Config-awareness (variant-aware BFM types) is a
  separate workstream; this plan does not change wrapper internals.
- The factory-key extension `(blockType, variant, configTag)` is
  settled by `plan-block-registration.md` and is not revisited.

## Done Criteria

- W1 / W2 / W3 / W7 proto results recorded in
  `research-block-registration-options.md` as a new dated decision
  entry.
- α / β / γ / δ decision recorded here under "Status".
- If δ: W5's δ branch landed (attribute macro + emission removals),
  W6 documentation cleanup landed (including the
  `--whole-archive` build-system policy doc), every example in
  `examples/` regenerates without any `force_link_*` emission,
  all current builds and runs pass without regression, the proto's
  matrix outcomes match expectations on every supported toolchain.
- If α: W5's α branch landed, W6 documentation cleanup landed,
  every example in `examples/` regenerates without any
  `force_link_*` emission, all current builds and runs pass without
  regression.
- If β: equivalent generator and documentation work for the project-
  aggregator path.
- If γ: scoped fix to `constructor.py` / `testbench.py` only; the
  open architectural issue documented as accepted technical debt.
