# Plan: Per-Block Trampoline Registration (T9, Option 9)

## Naming Note

Earlier revisions of this plan referred to the per-block "uses Config"
flag as `usesConfig`. The field has been renamed to
`isParameterizable` so that the same name is used across structures,
registers, memories, and blocks (a block carries
`isParameterizable: true` exactly when at least one structure on its
reachable surface is itself `isParameterizable: true`). See the
"Naming Note" in
[`plan-block-config-postprocess.md`](./plan-block-config-postprocess.md)
for the rationale. References to `usesConfig` in older review notes,
research documents, or commit messages refer to the same flag.

## Goal

Move `instanceFactory::registerBlock(...)` registration **for
parameterized blocks** into a generated per-block-per-project
trampoline TU, so that:

1. Generated parameterized-block files (`<block>.h`, `<block>.cpp`)
   are text-stable regardless of project and regardless of how many
   Configs the project binds to the block.
2. The registration lambda is parameterized on the `Config` type the
   project actually selects, instead of hard-coding `<block>DefaultConfig`.
3. The static-member-of-class-template hazard that breaks builds today
   (review items B1 and B2) is removed by construction.
4. Parent-container encapsulation is preserved and strengthened: each
   parameterized block's full class definition is reached from exactly
   one TU per project — its trampoline. Containers and the testbench
   see only `<child>Base.h`.
5. Verilated-variant registration and tandem-pair registration are
   absorbed into trampolines when they are project-specific, giving the
   project a single mechanical shape for every registration concern
   that cannot safely self-register from the block's own TU.

This plan supersedes the prior Option 1 (container-driven) approach.
The decision and rationale are recorded in
[`research-block-registration-options.md`](./research-block-registration-options.md)
under "Decision and Rationale (2026-05-05)."

## Interim Shape (2026-05-07, post Step 9)

The per-block trampoline TU now exists. Steps 4, 5, the SC-side of
Step 6, Step 8 (helloWorld validation), and Step 9 (templated-grandchild
regression in `examples/ip_test`) have landed. The verilated-wrapper
migration and Steps 10–12 (multi-Config-per-block, modules-mode
force-link, verilated-wrapper smoke) remain to do. Concretely, the
generator now produces, per project that has parameterized SC
blocks, one `<block>Registrar.cpp` per parameterized SC block:

- Emitted by a new `blockRegistrar` `fileMap` entry in
  `config/project.yaml` (`mode: block`,
  `cond: {isParameterizable: true}, condAnd: {hasMdl: true}`). The
  `isParameterizable` flag is a persisted column on the `blocks`
  table, populated by
  `pysrc/processYaml.py::projectCreate.calcBlockConfigInfo()` during
  YAML post-processing (see
  [`plan-block-config-postprocess.md`](./plan-block-config-postprocess.md)).
  `pysrc/newModule.py` reads it via `prj.getBlockConfigView(qualBlock)`
  for file-map `cond` evaluation without mutating the raw block
  schema data.
- Body written by `templates/systemc/blockRegistrar.py`. The
  trampoline `#include`s `<block>.h` plus the project's
  Config-policy headers and emits, for each variant the project's
  instance tree binds, a direct
  `instanceFactory::registerBlock("<B>_model", lambda, "<variant>",
  "<DefaultConfig>")` call with the Config-type stable string as the
  `configTag`. `addParam` calls for the block's variants are emitted
  alongside.
- `templates/systemc/constructor.py` and
  `templates/systemc/testbench.py` now thread the per-child
  `configTag` (the child block's `<DefaultConfig>` stable string)
  through every generated `instanceFactory::createInstance(...)`
  call for parameterized children. Non-templated children stay on
  `instanceFactory::noConfigTag` plus the active force-link call.
  Parameterized DUT lookups in the testbench template thread the
  matching `<DefaultConfig>` string.

Two registrations therefore coexist in `<block>.cpp` and the
`<block>Registrar.cpp` for parameterized blocks. The trampoline
entry is the load-bearing one — every generated caller looks it up
via the Config-name `configTag`. The retained in-block
self-registering static binds `noConfigTag` (now dormant — no caller
hits it) and serves a second purpose: its
`make_shared<<B><DefaultConfig>>(...)` expression forces implicit
template instantiation of `<B><DefaultConfig>`'s constructor body,
`regHandler`, etc. (defined later in the same `.cpp`), so the
trampoline TU — which sees only `<block>.h` declarations — can link
without unresolved external references. Removing this in-block
static fully requires either modules-mode `import <block>;` from
the trampoline (long-term plan) or a new GENERATED_CODE marker
appended to `<block>.cpp` after all template definitions for an
explicit instantiation; the latter would invalidate hand-written
tails in existing projects (`make reset` discards them) and is
deferred.

Implications and what is *still* not done:

- Closes review items B1 and B2 by construction. The trampoline TU
  has full class visibility for its lambda body; the in-class
  template static is gone.
- Multi-Config-per-project bindings remain unreachable. Reaching
  them requires per-instance Config propagation in
  `pysrc/processYaml.py` so the trampoline can emit one `(variant,
  Config, configTag)` tuple per instance binding rather than one
  per (variant, default Config) pair.
- Verilated wrappers still use the wrapper-local
  `struct registerBlock` / `static registerBlock_` shape, with the
  explicit specialization living in `verif/vl_wrap/vl_wrap.cpp`
  (only compiled under `VL_DUT=1`). The trampoline emitted by
  `blockRegistrar.py` deliberately does **not** include
  `<block>_hdl_sc_wrapper.h` — that header is on the include path
  only under VL_DUT=1, and the model-mode trampoline is built
  unconditionally. The verilated migration is a separate per-block
  trampoline that lives alongside `vl_wrap.cpp` in
  `verif/vl_wrap/`; that work is deferred. The `cond` predicate is
  scoped to `isParameterizable: true` so non-templated `hasVl` blocks
  gain no (empty) trampoline today.
- `<block>.cpp` for parameterized blocks is still project-specific
  (the long-term plan wants it text-stable). The remaining
  divergence is the in-block self-registering static.
- Step 7 textual confirmations (`<ip>_<ip_test>_registrar.cpp`)
  match the new shape modulo naming: the file is named
  `<block>Registrar.cpp` and lives in the project's `model/`
  directory. The `_<P>_` portion called out in Plan-1/Plan-2 is
  implicit in the path. Final naming remains a deferred decision.

Validation as of this revision (2026-05-06):

- `make -C proto/model step6` → `PASS: block registration prototype
  passed` (unchanged).
- `make -C builder/base/examples/helloWorld/model gen && make` runs
  all four tests (`test_rdy_vld`, `test_req_ack`, `test_push_ack`,
  `test_pop_ack`) cleanly — no trampoline TU is emitted because
  helloWorld is fully non-templated.
- `make -C builder/base/examples/ip_test gen` plus `make -C
  builder/base/examples/ip_test/rundir clean && make` builds clean
  with `model/ipRegistrar.cpp`, `model/ip_topRegistrar.cpp`, and
  `model/srcRegistrar.cpp` linked into the binary. Simulation
  initialises every instance through the factory and aborts on the
  pre-existing `tb.external.uAPBDecode.cpu_main` port-binding error
  unrelated to block registration.

The full Implementation Steps below remain authoritative for the
final shape. Step 4's caller reconciliation extension (multi-Config
per instance) and Steps 9–12 proceed in subsequent sessions.

## Scope: Prototype-Gated, Two Registration Triggers

T9 implementation is gated by a standalone prototype before generator
changes. The prototype lives in [`../../proto/model`](../../proto/model)
and validates the selected mechanics without touching `templates/`,
`pysrc/`, or generated project wiring:

- direct trampoline lambdas for parameterized blocks,
- stable string `configTag` keys,
- multi-Config registrations for the same `(blockType, variant)`,
- variant fallback scoped to the same `configTag`,
- active force-link calls for non-templated self-registration,
- and trampoline-owned registration for verilated-style wrappers.

The prototype target is:

```bash
make -C ../../proto/model step6
```

The selected architecture has two registration triggers:

- **Parameterized blocks** (`data['isParameterizable']` from `getBlockData()`
  is true) reach the factory through a **per-project trampoline
  TU**. The trampoline directly emits the
  `instanceFactory::registerBlock(...)` lambdas for each
  `(block, variant, Config)` the project's instance tree binds. There
  is no generated helper-function template whose body lives in another
  `.cpp`.
- **Pure non-templated SC blocks** reach the factory through a
  **self-registering static** in the block's own `.cpp` /
  module-implementation-unit. The self-registering static may call a
  non-templated helper for local clarity, but no project Config
  enumeration is involved.

Rationale for limiting SC trampolines to parameterized blocks:
trampolines exist to solve the per-project Config enumeration problem
and the encapsulation regression that comes with templated lambdas.
Pure non-templated SC blocks have neither problem. Designs that contain
only pure non-templated SC blocks therefore generate **no SC
trampoline TUs and no project-level SC registration artifact**, which
preserves today's "register from your own TU" property for those
projects.

**Non-templated self-registering blocks adopt an active force-link
function** in their base header / base-module interface to guarantee
static-init reachability under C++20 modules and static-library
linking. The active function is **not** emitted for parameterized SC
blocks; the trampoline already provides the linkage they need. The
force-link mechanics and documentation requirement are covered in
"Force-Link Function" below.

Mixed projects (parameterized and non-templated blocks side by side,
e.g., `ip_test` once T6 lands) carry both triggers concurrently. The
`instanceFactory` map sees registrations from trampoline statics
(parameterized blocks) and from self-registering statics
(non-templated blocks); both populate the same factory map and
coexist without interaction.

## Context

Today `templates/systemc/classDecl.py` emits a `struct registerBlock`
with a constructor that calls `instanceFactory::registerBlock(...)`,
plus a `static registerBlock registerBlock_;` declaration inside the
class body. The static is suppressed for parameterized blocks
(`constructor.py` line 53-55), and even when present the lambda
hard-codes `<block>DefaultConfig` (`classDecl.py` line 96). The
combined result is that a parameterized block cannot be reached
through the factory under any non-default `Config`, and the build
relies on lazy template instantiation to mask the missing static
definition (review items B1 and B2).

The new mechanism removes the in-class registrar entirely. Each
project gets one trampoline TU per parameterized block; the
trampoline is the only TU in the program with full visibility of
the block's class definition, and it owns every registration the
project needs for that block.

## Selected Architecture

### Per-block trampoline TU

For each parameterized block `B` that project `P` instantiates, the
generator emits a trampoline TU named `<B>_<P>_registrar.cpp` (final
naming convention is a deferred decision). The trampoline:

- Imports or includes the block's full class module / header.
- Imports or includes the project's Config policy types.
- Directly registers one lambda per `(B, variant, Config, configTag)`
  tuple the project's instance tree binds. The lambda constructs
  `make_shared<B<Config>>`.
- Carries an anonymous-namespace static whose constructor performs
  the registration calls.

The trampoline is unconditionally linked into the program, satisfying
static-init reachability under both classic-header and module modes.

The important shape is that the trampoline compiles the lambda body.
It has full class visibility and the selected Config type in one TU,
so there is no cross-TU function-template instantiation problem.

### Non-templated block registrar helper

Pure non-templated SC blocks may declare a non-templated free helper
function in their module interface (or header during the M3
transition):

```cpp
void register_<B>_variants();
```

The helper body is defined in the block's module implementation unit
(or `.cpp` during transition). It calls
`instanceFactory::registerBlock(...)` for each variant the block
declares, with a lambda that constructs `make_shared<B>`. Because the
helper is non-templated and project-independent, keeping its body in
the block implementation TU does not create the unreachable template
body hazard that the Stage 0 prototype ruled out for parameterized
registrations.

Parameterized SC blocks do **not** emit `register_<B>_variants<Config>`
helper templates. Their registration lambdas live directly in the
trampoline. The block's `.h`/`.cppm` and `.cpp`/module-implementation
unit remain text-stable across project changes because the trampoline
is the only artifact that enumerates project-bound Configs.

`instanceFactory::addParam({...})` remains Config-independent and is
emitted by the trampoline static for parameterized blocks and by the
non-templated helper for non-templated blocks. The parameter table
itself is taken from the block's YAML default Config (and from
variant-specific overrides where the YAML supplies them); it does
not need to enumerate project-bound Configs. Putting `addParam` in
the trampoline keeps every project-specific call to
`instanceFactory::*` in a single TU per (block, project). Putting it
in the non-templated helper keeps the same property for blocks that
have no trampoline. This resolves Plan-8.

### Self-registering static (non-templated blocks only)

For non-templated blocks, the helper is invoked at program start by a
self-registering static emitted into the block's own
`.cpp`/module-implementation-unit:

```cpp
namespace {
[[maybe_unused]] int _<B>_registered = (register_<B>_variants(), 0);
} // namespace
```

This preserves today's invariant for non-templated blocks: the block
registers itself from its own TU, with no project-level artifact. The
in-class `struct registerBlock` and the out-of-line
`registerBlock_` static definition (today's mechanism) are removed and
replaced by this single self-registering static.

Parameterized blocks emit no self-registering static and no templated
registration helper; their lambdas are emitted directly in the
per-project trampoline TU instead.

### Container `.cpp` / `.cppm`

Container files have **no registration code**. Containers see only
`<child>Base.h` for each direct child and call
`instanceFactory::createInstance(...)` at construction time. For a
parameterized child, the generated call supplies the child's
`configTag`. For a non-templated self-registering child, the generated
constructor emits an active `force_link_<child>()` call before the
first factory lookup that may need that child's TU.

The factory entries the container relies on are populated by
trampoline statics for parameterized / verilated registrations and by
self-registering statics for pure non-templated SC blocks, not by any
registration section in the container.

### Top-level testbench

`sc_main` keeps the same high-level flow. Generated testbench and
testbench-config code is migrated like other generated factory
callers: any `createInstance(...)` call for a parameterized DUT passes
the selected `configTag`, and any call that depends on a non-templated
self-registering block emits the corresponding active force-link call.
Trampoline registration runs before `main`; self-registration for
non-templated blocks is made reachable by the force-link calls before
the factory lookup executes.

### Factory-key extension

`instanceFactory::registerBlock` and `instanceFactory::createInstance`
are extended from `(blockType, variant)` to `(blockType, variant,
configTag)`. This supports realistic project workloads where the same
block is instantiated with two different Configs in the same project
tree (e.g., a camera IP at high and low resolution; a USB controller
at full and high speed).

The selected `configTag` encoding is a generator-assigned stable
string. The Stage 0 prototype used `ipDefaultConfig` /
`ipFastConfig` strings and validated that two Configs can share the
same `(blockType, variant)` without collision. A stable string is
preferred over `std::type_index` because it is deterministic in
generated text, easy to dump in diagnostics, and keeps map keys
serialisable.

Backward-compatible overloads remain:

- Existing `registerBlock(blockType, factoryFn)` and
  `registerBlock(blockType, factoryFn, variant)` overloads forward to
  the extended API with a generator-reserved sentinel
  `noConfigTag` (working spelling: `"__a2c_no_config__"`).
- Existing `createInstance(..., variant)` overloads forward with the
  same sentinel.
- New generated callers for parameterized blocks pass the selected
  Config's stable tag explicitly.

Lookup order is:

1. Exact `(blockType, variant, configTag)`.
2. Fallback `(blockType, "", configTag)`.
3. Error.

There is intentionally no fallback across different `configTag`
values. The Stage 0 prototype validated this by accepting
variant fallback for `ipDefaultConfig` while rejecting fallback from
`ipFastConfig` to the default Config entry.

All `createInstance` callers are generated, so the migration is
mechanical. The affected templates include `constructor.py`,
`testbench.py`, `fileGen.py`, `module_hdl_wrapper.py`, and
`blockRegs.py`.

## Modules Layout

The baseline T9 implementation keeps the block class exported when
the trampoline is an ordinary `.cpp` / importing TU. In that shape,
the trampoline can legally name `B<Config>` because it imports or
includes the same public class surface available in header mode.

Selective export is a later module-layout refinement, not a baseline
assumption. If the block class becomes module-internal, the trampoline
must be generated as a module implementation unit or partition of the
block module so it can legally name the non-exported class. A plain
external importer cannot construct a module-internal `B<Config>`.

Both baseline and selective-export shapes satisfy static-init
reachability as long as the trampoline object is unconditionally
linked into the program.

## Force-Link Function

> **Historical / retired (2026-06-23).** The active `force_link_<block>()`
> function described in this section was retired in favour of **Option δ**
> — a `[[gnu::used, gnu::retain]]` retain attribute
> (`A2C_REGISTRATION_RETAIN`) on the self-registering static plus an
> explicit build-system contract for archive packaging. The generator no
> longer emits any `force_link` declaration, definition, or call. See
> [`plan-registration-encapsulation-cleanup.md`](./plan-registration-encapsulation-cleanup.md)
> and the "Decision Addendum (2026-06-23)" in
> [`research-block-registration-options.md`](./research-block-registration-options.md)
> for the proto matrix, the retirement rationale, and the
> `--whole-archive` build-system contract. The remainder of this section
> is preserved for historical context only.

### Purpose

Under classic headers, every `.cpp` the build compiles is also linked
into the program, so a static initialiser inside `<block>.cpp` is
guaranteed to run before `main`. C++20 modules dissolve that
guarantee: an `import <block>;` does not by itself force the linker
to pull in the block's module-implementation unit. If nothing in the
program references a symbol from that unit, the build system is
permitted to omit it from the link and the static initialiser inside
it never fires.

For non-templated blocks this is a real correctness problem. The
self-registering static lives in the block's `.cpp`. Parents reach
the block through `instanceFactory::createInstance(...)` — a
string-keyed lookup — and never name the block's class symbol from
their own TU. Under modules, the linker may legitimately drop the
block's TU. The registration never runs and `createInstance` fails
at runtime with an "unregistered block type" error.

The force-link function restores the classic-header guarantee in a
portable C++ way that does not depend on compiler-specific section
attributes (`__attribute__((used))`, `.init_array`, etc.) or
build-system force-link rules.

### Mechanism

For each non-templated self-registering block, the generator emits two
pieces plus generated call sites:

- **In `<block>Base.h` (or the base-module interface unit — whichever
  surface every parent already imports for the block's port and
  signal declarations):**

  ```cpp
  // ===== Force-link function =====
  // Generated callers invoke force_link_<block>() before factory
  // lookups that may construct <block>. The call creates a real
  // relocation to <block>.cpp / the <block> module implementation
  // unit, forcing that object into the program. This is required
  // under C++20 modules and static-library linking, where 'import'
  // alone does not guarantee that an imported module's implementation
  // unit is linked. Without this call, the self-registering static
  // inside <block>.cpp may not fire and the block may be unreachable
  // through the factory.
  //
  // Generated by templates/systemc/blockRegistrar.py. Do not edit.
  // See plan-block-registration.md "Force-Link Function" for the full
  // rationale.
  void force_link_<block>();
  // ===== End force-link function =====
  ```

- **In `<block>.cpp` (or the block's module-implementation unit):**

  ```cpp
  // Force-link function. Declaration in <block>Base.h.
  // See plan-block-registration.md "Force-Link Function".
  void force_link_<block>() {}
  ```

- **In generated parent/testbench code before the relevant factory
  lookup:**

  ```cpp
  force_link_<block>();
  auto child = instanceFactory::createInstance(...);
  ```

The generated call is the important part. It creates an unresolved
symbol reference from a linked parent/testbench TU to the child's
implementation TU. If the child object is inside a static archive, the
linker must extract it to satisfy that reference; once extracted, the
self-registering static in the same object runs before `main`.

The Stage 0 prototype validates this shape by placing the
non-templated `apbDecode` registration object in a static archive and
requiring the test binary to call `force_link_apbDecode()` before
`createInstance(...)`.

The previous passive inline-variable anchor is intentionally rejected.
An unused inline variable in a base header can be optimised away or
avoid emitting a relocation from the including TU, so it does not
prove that the implementation object is linked.

### Applies to which blocks

- **Non-templated self-registering SC blocks: required.** The
  self-registering static is the registration trigger; the active
  force-link call guarantees that the TU containing it is linked.
- **Parameterized SC blocks: not required for registration.** The
  per-project trampoline owns the registration lambdas and directly
  references `make_shared<B<Config>>`.
- **Verilated wrappers registered by trampoline: not required for
  registration.** Their trampoline is linked directly and references
  the concrete wrapper alias.

If a future change introduces other static-init side effects in a
parameterized block's implementation unit that need to run regardless
of the trampoline path, the force-link function pattern remains
available as a local fix.

### Generator documentation requirement

The template that emits the force-link function carries a Python-side
comment block explaining the mechanism, when it applies, and why it
is emitted. The exact comment text is:

```python
# Force-link function (active successor to Option 6a's passive anchor)
#
# Emits a void force_link_<block>() declaration in <block>Base.h and a
# matching no-op definition in <block>.cpp. Generated parent/testbench
# code calls this function before factory lookups that may construct a
# non-templated self-registering block. The call creates a real symbol
# reference to <block>.cpp, forcing the linker to pull that object into
# the program even when nothing else references symbols from it.
#
# This is required under C++20 modules and static-library linking,
# where importing a base interface or using string-keyed factory lookup
# does not guarantee that the block implementation object's static
# initializers run. Without the active call, the self-registering
# static inside <block>.cpp can remain unfired and
# instanceFactory::createInstance can fail at runtime.
#
# Emitted only for non-templated self-registering SC blocks.
# Parameterized blocks and trampoline-owned verilated wrappers reach
# registration through a linked trampoline TU instead.
#
# See plan-block-registration.md "Force-Link Function".
```

The corresponding generated comment block is reproduced in the
emitted base header so a developer reading the generated code
understands the function's role without consulting external docs.

### Cost

- One function declaration in `<block>Base.h` plus a comment block.
- One no-op function definition in `<block>.cpp` plus a comment.
- One generated call at each parent/testbench creation site that may
  need the non-templated block's self-registration.
- One additional symbol per non-templated self-registering block in
  the program. The symbol name is generator-controlled
  (`force_link_<block>`) and is linkage plumbing, not user API.

Open Question 11 in the research doc records the original passive
anchor trade-off. This plan selects the active force-link function
because the Stage 0 prototype proved it creates a real reference,
whereas a passive inline variable is not reliable enough for modules
or archive linking.

### Encapsulation follow-up

After Stage 4.4 / Stage 9.3 of
[`plan-variant-config-unification.md`](./plan-variant-config-unification.md)
landed, the per-block trampoline shape used by parameterized SC
blocks (one `<block>Registrar.cpp` per block, unconditionally linked
by the project Makefile) made the asymmetry with the non-templated
self-registering path concrete in generated code:

- Templated SC blocks: registration lives in the trampoline TU.
  Parents have no compile-time symbol reference to the child's TU.
- Non-templated SC blocks: registration lives in `<block>.cpp`.
  Parents emit `force_link_<block>()` calls (currently as a comma-
  operator inside the mem-initialiser) to extract the child's TU
  from a static archive under modules. The parent now carries a
  compile-time symbol reference to every non-templated child.

This weakens the factory's encapsulation contract for the non-
templated half of blocks. The Stage 0 prototype validated the
*mechanics* of the active force-link function but did not surface
the encapsulation cost, did not exercise tandem mode, and did not
investigate whether the trampoline pattern (already proven for
parameterized SC blocks and verilator wrappers) could subsume the
non-templated path uniformly.

The follow-up plan that revisits this trade-off — proposing options
to retire the force-link mechanism in favour of a universal per-
block trampoline (α), a project-level aggregator (β), or a cosmetic
emission cleanup (γ) — is recorded in
[`plan-registration-encapsulation-cleanup.md`](./plan-registration-encapsulation-cleanup.md).
Verilator and tandem coverage gaps from the original prototype are
tracked there as W1 / W2 / W3.

<!--
Historical passive-anchor text replaced by the active force-link
function design after Stage 0 prototype validation.
-->

## Factory Suffix Taxonomy

The `instanceFactory::createInstance` lookup key is
`blockTypeUser + "_" + suffix`, where the suffix is chosen by the
factory at lookup time, not by the registrar:

- **`_model`** — default SC behavioural block (parameterized or not).
  Selected when no `registerInstance(qualifiedName, ...)` override
  applies and the call is `INSTANCE_FACTORY_DEFAULT`.
- **`_verif`** — verilated wrapper, custom BFM, or other verification
  override. Selected when an instance has been mapped via
  `registerInstance(qualifiedName, "verif")`. This is the suffix the
  current generator already uses for `<block>_hdl_sc_wrapper`
  registration (see `templates/systemc/module_hdl_wrapper.py`).
- **Tandem-mode strings** — `INSTANCE_FACTORY_PRIMARY_TYPE` and
  `INSTANCE_FACTORY_SECONDARY_TYPE` resolve to whatever names the
  build set via `setInstanceFactoryMode`. The suffix is therefore
  build-mode-controlled, not chosen by the trampoline.

The trampoline must register each block under the **same suffix the
factory will look up at the call site.** The suffix is not part of the
trampoline's design freedom; it is dictated by the API. Generated
trampolines therefore emit one entry per
`(suffix, variant, configTag)` tuple the project's instance tree
needs.

`configTag` is orthogonal to the suffix. A single block can be
registered as both `<B>_model` (under one or more `configTag` values
for parameterized SC paths) and `<B>_verif` (under `noConfigTag` for
today's non-templated verilated wrapper, or under a `configTag` if and
when verilated wrappers become Config-aware). The factory key is
`(blockType, variant, configTag)` where `blockType = <B>_<suffix>`,
so suffix and Config tag never collide.

## Verilated and Tandem Registration

Verilated blocks (SC wrappers around Verilator-compiled SystemVerilog)
are registered by trampolines whenever `hasVl` is true. This applies
whether or not the corresponding SC model block uses Config. The
current wrapper-local `struct registerBlock` / `registerBlock_`
mechanism is removed for verilated wrappers so there is one
project-specific owner for wrapper registration.

The trampoline:

- Includes `<block>_hdl_sc_wrapper.h` and references the per-variant
  `using` aliases (`<block>_<variant>_hdl_sc_wrapper`).
- Registers each `(block, variant)` pair under the extended factory
  key, using the **`_verif` suffix** to match the existing factory
  resolution rule (see "Factory Suffix Taxonomy" above). Today's
  generator already registers verilated wrappers as
  `<block>_verif`; the trampoline preserves that contract. Verilated
  wrappers that are not Config-templated use `noConfigTag`; wrappers
  that become Config-aware later use the same stable string
  `configTag` as SC-only parameterized blocks.

The Stage 0 prototype includes a verilated-style trampoline that
registers a concrete `blockF_variant0_hdl_sc_wrapper` alias under
`blockF_verif` and exercises the verif lookup path through a
production-shaped `createInstance` resolver.

Tandem registration (RTL/model and model/model paired builds) is
also reified in the trampoline. The exact record shape — paired
factory entry, side-table, or build-mode-selected entry — is a
prototype-stage decision (Plan-9). The suffix on the registered key,
however, is **not** a Plan-9 choice: it is whatever
`setInstanceFactoryMode` produces for `INSTANCE_FACTORY_PRIMARY_TYPE`
and `INSTANCE_FACTORY_SECONDARY_TYPE`. The trampoline must emit those
suffixes verbatim. Folding tandem registration into the trampoline is
consistent with the trampoline's role as the single place where every
project-specific registration concern for the block lives.

## Generator Changes

### Removals (all blocks)

- **`templates/systemc/classDecl.py`** — remove emission of
  `struct registerBlock`, `static registerBlock registerBlock_;`, and
  the per-class `addParams` helper for **both** parameterized and
  non-templated SC blocks. Parameterized registration moves directly
  into trampolines (which also own the `addParam` calls for those
  blocks, per Plan-8 above); pure non-templated SC registration moves
  into the new non-templated helper / self-registering static, which
  also emits `addParam`.
- **`templates/systemc/constructor.py`** — remove the existing
  `if not isParameterizable:` branch that emits the out-of-line
  `registerBlock_` definition (line 53-55 today). The non-templated
  SC block's registration trigger becomes the new self-registering
  static emitted by the non-templated registrar support template
  instead. Keep
  `SC_HAS_PROCESS({className})` emission unchanged for both paths.
- **`templates/systemc/module_hdl_wrapper.py`** — remove wrapper-local
  `struct registerBlock` / `registerBlock_` emission. Verilated
  wrapper registration is emitted by the per-block trampoline when
  `hasVl` is true.

### New template — block registrar support

A new template (working name `templates/systemc/blockRegistrar.py`)
emits non-templated registrar support only:

- The helper function declaration into the block's `.h`/`.cppm` for
  pure non-templated SC blocks.
- The corresponding helper definition into the block's
  `.cpp`/module-implementation unit.
- The active force-link function declaration in the base header and
  no-op definition in the implementation unit.

For non-templated blocks, the template additionally emits the
self-registering static into the implementation unit:

```cpp
namespace {
[[maybe_unused]] int _<B>_registered = (register_<B>_variants(), 0);
} // namespace
```

Parameterized blocks emit no self-registering static; the trampoline
emits their factory lambdas directly. No
`register_<B>_variants<Config>` helper template is generated.

Inputs from `data`:

- `data['blockName']`
- `data['variants']` (parameter table for `addParam`)
- `data['isParameterizable']`, `data['defaultConfig']`, and
  `data['configTag']` (assembled by `getBDConfigInfo`;
  `isParameterizable` and `defaultConfig` are persisted columns on
  the `blocks` row, populated by
  `projectCreate.calcBlockConfigInfo()`)

Outputs:

- Header / interface unit: helper declaration for pure
  non-templated SC blocks only.
- Base header / base-module interface: active force-link function
  declaration for non-templated self-registering blocks.
- Implementation unit / `.cpp`: helper body; for non-templated
  blocks, also the force-link definition and the self-registering
  static.

The Python-side comment in this template documents the active
force-link mechanism and the registration-trigger split (trampoline vs
self-registering static) per the verbatim comment block in
"Generator documentation requirement" above.

### New template — per-project trampoline

A new top-level generator pass emits one trampoline TU per
block per project when the block has parameterized SC registration or
verilated wrapper registration. Pure non-templated SC-only blocks are
skipped — they self-register from their own TU, made reachable by the
active force-link function. Projects whose blocks are all pure
non-templated SC-only blocks gain no project-level registration
artifact.

Naming convention (working): `<B>_<P>_registrar.cpp` or
`<B>_<P>_registrar.cppm`, placement deferred (Plan-1).

Inputs from project-level data:

- The set of `(B, variant, Config, configTag)` tuples in the
  project's instance tree for parameterized blocks only (filtered by
  `data['isParameterizable']`, sourced from the persisted
  `blocks.isParameterizable` column or read via
  `getBlockConfigView(qualBlock)` for project-level walks).
- The set of verilated variants for each `hasVl` block. Verilated
  wrappers are trampoline-owned even when the SC model block is not
  Config-templated.
- The set of tandem pairs for parameterized blocks (when tandem is
  in scope for the project).

**Variant-emission rule.** Each project YAML declares whether a
block has variants. When a block declares variants, every instance of
that block in the project's tree must specify a variant string, and
the trampoline emits one `registerBlock(...)` entry per
`(variant, Config)` pair under that variant string. When a block
declares no variants, the trampoline emits one entry per Config under
`variant = ""`. The trampoline never emits both forms for the same
block. The factory's "" fallback at lookup time is therefore a
defensive secondary path; correct generated code never relies on it.

`addParam` calls are emitted by the trampoline alongside
`registerBlock` calls. The parameter table is derived from
`data['variants']` and is Config-independent, so it is emitted once
per `(B, variant)` pair regardless of how many Configs the project
binds. For pure non-templated SC blocks, `addParam` calls are emitted
by the non-templated helper instead — those projects gain no
trampoline.

In the snippet below, `<B>` and `<P>` are generator placeholders for
the block name and project name; they are not C++ header-unit syntax.

Trampoline body:

```cpp
// generated <B>_<P>_registrar.cpp
import <B>;            // or #include "<B>.h" during transition
import <P>_configs;    // project Config policy types

namespace {
struct _<B>_<P>_registrar {
    _<B>_<P>_registrar() {
        // Parameter table — Config-independent, emitted once per
        // (B, variant). Source: data['variants'] from the block YAML.
        instanceFactory::addParam({ /* <variant>: name -> value pairs */ });

        // SC-model lambdas — one per (variant, Config) tuple bound by
        // the project's instance tree. When the block has no variants,
        // the variant string is "".
        instanceFactory::registerBlock(
            "<B>_model",
            [](const char* n, const char* v, blockBaseMode m) {
                return std::static_pointer_cast<blockBase>(
                    std::make_shared<<B><Config1>>(n, v, m));
            },
            "<variant>",
            "<Config1Tag>");
        instanceFactory::registerBlock(
            "<B>_model",
            [](const char* n, const char* v, blockBaseMode m) {
                return std::static_pointer_cast<blockBase>(
                    std::make_shared<<B><Config2>>(n, v, m));
            },
            "<variant>",
            "<Config2Tag>");
        // verilated variants (registered under the _verif suffix, which
        // is what the factory's instance-mode resolution uses for
        // verification overrides — see "Factory Suffix Taxonomy"):
        instanceFactory::registerBlock(
            "<B>_verif",
            [](const char* n, const char* v, blockBaseMode m) {
                return std::static_pointer_cast<blockBase>(
                    std::make_shared<<B>_<variant1>_hdl_sc_wrapper>(n, v, m));
            },
            "<variant1>",
            instanceFactory::noConfigTag);
        // tandem pairs (shape TBD, Plan-9; suffix comes from
        // setInstanceFactoryMode, see "Factory Suffix Taxonomy"):
        // register_<B>_tandem_pair(...);
    }
};
_<B>_<P>_registrar _<B>_<P>_registrar_instance;
} // namespace
```

The contents are deduped over `(B, variant, Config)` for SC entries
and over `(B, verilatedVariant)` for `_verif` entries, then sorted
ascending for stable diffs. `configTag` is functionally derived from
Config and does not need to appear in the dedup key.

### `instanceFactory` API

`common/systemc/instanceFactory.{h,cpp}` is extended:

- `registerBlock(blockType, factoryFn, variant, configTag)` — new
  overload. Existing overloads stay and forward with
  `instanceFactory::noConfigTag`. The internal map keys on
  `(blockType, variant, configTag)`.
- `createInstance(..., variant, configTag)` — new overload. Existing
  overloads stay and forward with `instanceFactory::noConfigTag`.
- Lookup first checks `(blockType, variant, configTag)`, then
  `(blockType, "", configTag)`, then reports an unregistered block.
  It never falls back across `configTag` values.
- The `addParam` and lookup helpers remain unchanged in shape.

The first-write-wins behaviour stays as a soft guard against
accidental double-registration, with an optional debug-build assert
on differing factory targets (a useful future hardening; not a T9
gate).

### `templates/fileGen/fileGen.py`

- Remove the in-class registrar and out-of-line static markers from
  the block-`.cpp` and block-`.h` skeletons.
- Add a generator pass that emits the per-block trampoline TU into
  the chosen artifact directory (Plan-1).

### `config/project.yaml`

- Register the new block registrar support template under `templates:`.
- Register the trampoline emission under the project-level generator
  pass.

## Implementation Steps

1. Extend `instanceFactory` API for the `configTag` key. Encoding to
   use generator-assigned stable strings. Non-templated callers
   supply the sentinel `instanceFactory::noConfigTag` via existing
   forwarding overloads.
2. Add the non-templated block registrar support template. Outputs:
   - Helper declaration in `<block>.h`/`.cppm` for pure
     non-templated SC blocks.
   - Helper body in `<block>.cpp`/module-implementation-unit for
     pure non-templated SC blocks.
   - For non-templated blocks: the self-registering static in the
     implementation unit.
   - For non-templated blocks: the active force-link function
     declaration in `<block>Base.h` and definition in the
     implementation unit. The
     generated comment block (verbatim text in "Generator
     documentation requirement" above) is included in both
     locations.
3. Update `templates/systemc/classDecl.py` and
   `templates/systemc/constructor.py` to remove the in-class
   `struct registerBlock` and the out-of-line `registerBlock_` static
   definition for **all** blocks. Keep `SC_HAS_PROCESS(...)` emission.
4. Add the trampoline generator pass: project instance walk emits
   one trampoline per block that needs parameterized SC registration
   or `hasVl` wrapper registration, deduped and sorted. Pure
   non-templated SC-only blocks are filtered out of the walk for this
   pass.
5. Update `templates/fileGen/fileGen.py` and `config/project.yaml`
   to wire the new template and the project-level pass.
6. Update every generated factory caller (`constructor.py`,
   `testbench.py`, `fileGen.py`, `module_hdl_wrapper.py`, and
   `blockRegs.py`) to pass `configTag` for parameterized blocks and
   emit active force-link calls before non-templated self-registering
   block lookups.
7. Regenerate `examples/ip_test`. Confirm:
   - **Parameterized blocks** (e.g., `ip`):
     - `ip.h` has no `struct registerBlock` and no
       `registerBlock_` static.
    - `ip.h` does **not** carry a `register_ip_variants<Config>`
      helper declaration; parameterized registration lambdas are
      emitted directly in the trampoline.
     - `ipBase.h` does **not** carry a force-link function (force-link is
       suppressed for parameterized blocks).
     - `ip.cpp` has no out-of-line `registerBlock_` definition and
       no self-registering static (registration runs from the
       trampoline).
     - The project-level pass produces
       `<ip>_<ip_test>_registrar.cpp` (final name TBD) containing
       the anonymous-namespace static and direct
       `instanceFactory::registerBlock(...)` lambdas for each
       `(variant, Config, configTag)` the project's tree binds, plus
       the `instanceFactory::addParam(...)` calls for the block's
       variants.
   - **Non-templated blocks** (e.g., `apbDecode`):
     - `apbDecode.h` has no `struct registerBlock` and no static
       member; it carries the new `register_apbDecode_variants()`
       helper declaration.
     - `apbDecodeBase.h` carries the force-link function declaration
       with the verbatim explanatory comment block.
    - `apbDecode.cpp` carries the helper body (which calls
      `instanceFactory::registerBlock` and
      `instanceFactory::addParam`), the force-link function
      definition, and the self-registering static
       `[[maybe_unused]] int _apbDecode_registered = ...;`.
     - No trampoline is emitted for `apbDecode`.
   - `ip_top.cpp` and other container files contain no
     registration code; they include only `<child>Base.h`.
   - The build links and runs; `instanceFactory::createInstance(...)`
     returns instances of the correct `(block, Config)` shape for
     parameterized children and the correct instance for
     non-templated children.
8. Regenerate one fully non-templated example (`examples/helloWorld`,
   which contains no parameterized or `hasVl` blocks). Confirm:
   - No trampoline TU is emitted; no project-level registration
     artifact appears.
   - The block files carry the helper, the force-link function, and
     the self-registering static as described above.
   - The build links and runs against the new helper / force-link
     surface.

   Note: `examples/mixed` is **not** the example to use for this
   step, because it contains `hasVl` blocks whose verilated wrappers
   produce trampolines under T9. `mixed` is exercised separately in
   Step 12.

   **Outcome (2026-05-06).** Validated end-to-end. Regen on
   `helloWorld` initially exposed a separate pre-existing latent bug
   in `baseClassDecl.py` and `classDecl.py`: their include-emission
   loops only consulted `include_cppm` and hard-coded `import
   <module>;`, dropping the `#include "<projectIncludes>.h"` line
   that header-mode projects need. The fix added a header-mode
   fallback: when a context has no `include_cppm` entry but does have
   an `include_hdr` entry, emit `#include "<projectIncludes>.h"`
   instead of nothing. ip_test (cppm-only) is unaffected; helloWorld
   (hdr-only) regenerates correctly. After the fix, helloWorld
   regenerates with the expected helper / force-link /
   self-registering-static shape, builds clean, and runs all four
   tests (`test_rdy_vld`, `test_req_ack`, `test_push_ack`,
   `test_pop_ack`) to completion.
9. Add the templated-grandchild regression test (carried over from
   the prior plan): `ipLeaf` instantiated by `ip` proves the
   trampoline mechanism reaches deep descendants because the project
   walk emits a trampoline for `ipLeaf` directly. No per-block
   recursion is required.

   **Outcome (2026-05-07).** Validated end-to-end. `ipLeaf` is defined
   in its own `arch/yaml/ipLeaf.yaml` (own `LEAF_DATA_WIDTH` /
   `LEAF_MEM_DEPTH` parameters, own `ipLeafDataT` parameterizable type,
   own `ipLeafMemSt` structure, own private `ipLeafMem` memory with
   `regAccess: false` to anchor `isParameterizable: true`). Including
   `ipLeaf.yaml` from `ip_top.yaml` and adding `uLeaf:
   { container: src, instanceType: ipLeaf, variant: variantLeaf0 }`
   places `uLeaf` at depth `tb.ip_top.uSrc.uLeaf` — a templated
   grandchild reachable only through a parent-internal createInstance
   call.

   The plan literal called for `container: ip`. Routing `uLeaf` through
   `src` instead avoids triggering the auto-synthesised `ipRegs`
   register-decoder block that fires whenever a register-bearing block
   (like `ip`) gains its first child instance. That auto-synth path is
   currently buggy (duplicate `(uIpRegs, ip, ipRegs)` instance rows in
   the project DB and an unresolved `uIp0->ipCfg(...)` reference in
   `ip.cpp`'s generated body); fixing it is a separate ticket. Routing
   through `src` preserves the test's intent — the project walk
   discovers a new templated block at deeper instance depth and emits
   `model/ipLeafRegistrar.cpp` directly — without depending on the
   container-with-registers code path.

   The regression also exposed three latent bugs in shared templates
   that were repaired alongside the Step 9 work:
   - `templates/systemc/module_hdl_wrapper.py` read
     `data['isParameterizable']` unconditionally; at hierarchy-mode rendering
     (`vl_wrap.cpp`) the project-level `data` dict has no per-block
     keys. Fixed by `data.get('isParameterizable', False)` plus a comment
     recording the two render contexts.
   - `templates/systemc/headers.py` interleaved `import <ctx>;` /
     `using namespace <ctx>_ns;` lines per-context. Two or more imported
     contexts then placed a `using` between two `import`s, which C++20
     forbids in a module-interface unit's purview. Fixed by emitting
     all `import`s first, then all `using namespace` directives.
   - `templates/systemc/baseClassDecl.py` emitted the leading `:` on
     the base-class constructor only when `port_count > 0`. A
     parameterized block with parameters but no ports therefore
     produced `B(std::string, const char *)
         PARAM(...)` (no colon). Fixed by computing
     `colon = ':' if port_count > 0 or has_param_inits else ''`.

   Validation:
   - `make -C builder/base/examples/ip_test gen` is clean.
   - `model/ipLeafRegistrar.cpp` contains
     `instanceFactory::registerBlock("ipLeaf_model", ..., "variantLeaf0",
     "ipLeafDefaultConfig")` plus the `addParam` table for
     `LEAF_DATA_WIDTH` / `LEAF_MEM_DEPTH`.
   - Full clean build links `ipLeaf.o` and `ipLeafRegistrar.o`.
   - Runtime startup shows `ipLeaf:Instance tb.ip_top.uSrc.uLeaf
     initialized.` and `ipLeaf:Instance tb.external.uSrc.uLeaf
     initialized.`, confirming both `createInstance(...,
     "ipLeafDefaultConfig")` lookups resolved through the trampoline.
   - The simulation later aborts on the pre-existing
     `tb.external.uAPBDecode.cpu_main` port-binding error noted under
     "Interim Shape (2026-05-06)"; that failure is unrelated to block
     registration.
10. **Absorbed by
    [`plan-variant-config-unification.md`](./plan-variant-config-unification.md)
    Stage 8.1.** The original Step 10 (multi-Config-per-block
    regression) framed Configs as orthogonal to variants. Path C
    unifies the two dimensions (variant ≅ Config); the regression
    now exercises two variants binding to two Config policies under
    the simplified `(blockType, variant)` factory key. The
    `configTag` infrastructure that Step 10 originally relied on
    retires under Path C. See the unification plan for the full
    work plan and the
    [`research-multi-config-bindings.md`](./research-multi-config-bindings.md)
    research doc for the design rationale.
11. Add a modules-mode force-link regression: build a non-templated block
    as `.cppm` (when M3 lands) and confirm `createInstance` succeeds.
    Repeat with the force-link call temporarily disabled in the generator and
    confirm the build either fails to link or produces a runtime
    "unregistered block type" error. The contrast confirms the force-link call
    is doing real work and not a no-op.
12. Add a verilated-wrapper registration smoke using a `hasVl` block
    (e.g., `examples/mixed`) and confirm wrapper registration comes
    from the trampoline, not wrapper-local `registerBlock_`.

## Verification

```bash
make -C ../../proto/model step6

python3 -m py_compile \
  templates/systemc/blockRegistrar.py \
  templates/systemc/classDecl.py \
  templates/systemc/constructor.py \
  templates/fileGen/fileGen.py \
  pysrc/intf_gen_utils.py

rm -rf examples/ip_test/.gen
make -C examples/ip_test gen
make -C examples/ip_test/rundir clean
make -C examples/ip_test/rundir
```

After the build succeeds:

- Inspect the generated `ip.h` / `ip.cppm` and `ip.cpp` / module
  implementation unit to confirm text stability across project
  changes.
- Confirm the Stage 0 prototype prints
  `PASS: block registration prototype passed` before making generator
  changes.
- Inspect a non-templated block's generated `<block>Base.h` to confirm
  the force-link function declaration plus the verbatim explanatory
  comment block are present.
- Inspect a non-templated block's generated `<block>.cpp` to confirm
  the helper body, the force-link function definition, and the self-registering
  static are present, and that the force-link function carries the explanatory
  comment.
- Inspect a parameterized block's generated `<block>Base.h` to
  confirm the force-link function is **not** present.
- Run the existing `ip_test` smoke. Confirm
  `instanceFactory::createInstance("ip", "variant0", configTag)`
  returns a valid `ip<ipDefaultConfig>` instance and
  `instanceFactory::createInstance("apbDecode", ...)` returns the
  expected non-templated instance.
- Run the `ipLeaf` grandchild regression to confirm transitive
  coverage via the project walk's trampoline emission.
- Run the multi-Config-per-block regression to confirm the
  factory-key extension actually distinguishes Configs.
- Run the modules-mode force-link regression (Implementation Step 11) to
  confirm the active function call is doing real work under modules.
- Add a regression that registers `ip<MyConfig>` (a Config with
  non-default `IP_DATA_WIDTH`) and verifies `createInstance(...)`
  returns an instance whose pack/unpack uses `MyConfig::IP_DATA_WIDTH`.
  This regression doubles as coverage for review items B3 and B4.

## Deferred Decisions (Plan Stage)

Tracked here so they are not lost. The Stage 0 prototype settled the
core C++ mechanics; the remaining items are generator / build-system
layout decisions:

- **Plan-1: Trampoline placement.** `build/` vs. checked-in per-project
  IP-config directory vs. source-tree-adjacent location. Tied to the
  M3 build-system refactor. **Invariant for any chosen layout:** the
  trampoline TU must be linked directly into the program. Packaging
  trampolines into a static archive would reintroduce the linker-strip
  hazard the active force-link function solves for non-templated
  blocks. If a future Plan-1 outcome forces archive packaging, the
  same force-link mechanism must be extended to trampolines.
- **Plan-2: Trampoline naming convention.** Must avoid collisions
  across projects when multiple projects share a workspace.
- **Plan-3: Module unit shape for trampolines.** Plain `.cpp`, module
  implementation unit, or module partition.
- **Plan-4: Selective export adoption.** Whether the block class
  becomes module-internal during the M3 transition or stays exported
  for parity with header-mode.
- **Plan-5: Where Config policy types are defined and how the
  trampoline reaches them.** Likely a per-project Config module or
  header.
- **Plan-6: Generator architecture for the trampoline pass.** Which
  generator owns it; regeneration triggers.
- **Plan-7: `configTag` encoding — settled by Stage 0.** Use a
  generator-assigned stable string plus the reserved
  `instanceFactory::noConfigTag` sentinel for non-templated callers.
- **Plan-8: `addParam` placement — settled.** For parameterized
  blocks `addParam` is emitted by the trampoline static alongside
  `registerBlock` calls. For pure non-templated SC blocks `addParam`
  is emitted by the non-templated helper. The parameter table is
  Config-independent and is taken from `data['variants']`.
- **Plan-9: Tandem registration record shape.** Paired factory entry,
  side-table, or build-mode-selected entry.

## Migration Notes

- T9 ships value once T6 (block templating) and T7 (Config struct
  generation) are in place. Both are tracked in
  [`plan-development-ordering.md`](./plan-development-ordering.md).
- **Non-templated blocks change shape but not behaviour.** The
  in-class `struct registerBlock` and the out-of-line `registerBlock_`
  static are removed and replaced by a free helper function plus a
  self-registering static in the block's `.cpp`. The block continues
  to register itself from its own TU; no project-level artifact is
  required. Non-templated-only projects (`examples/helloWorld`,
  `examples/mixed`'s non-templated portions) gain no trampoline TU
  and no project-level registrations file.
- **The active force-link function is new surface in `<block>Base.h`
  for every non-templated self-registering SC block.** The function is
  required for modules-mode and static-archive correctness, costs one
  declaration plus a comment in the base header, one no-op definition
  plus a comment in the implementation unit, and one generated call at
  relevant factory lookup sites. It is generator-controlled linkage
  plumbing, not a user-facing API.
- Mixed projects (parameterized and non-templated blocks side by
  side, such as `ip_test` once T6 lands) carry both triggers
  concurrently: trampoline statics for parameterized blocks,
  self-registering statics for non-templated blocks. Both populate
  the same `instanceFactory` map and coexist without interaction.
- Container files become simpler under this plan than under Option 1:
  no generated registration section is added to container `.cpp` /
  `.cppm` files. This applies to containers regardless of whether
  their children are parameterized or non-templated.
- The `instanceFactory` API extension to carry a `configTag` key
  remains backward-compatible for non-templated callers. Existing
  overloads forward to the stable-string sentinel
  `instanceFactory::noConfigTag`.

## Tactical Workaround History (2026-05-01)

A tactical workaround for B1/B2 was attempted on 2026-05-01 by adding
an explicit specialization of `registerBlock_` to the hand-written
tail of `ip.cpp`, `src.cpp`, and `ip_top.cpp`. The workaround
exposed an entangled T6 generator defect (a missing `typename` on a
dependent qualified-id in `constructor.py`) and was not landed.

Decision: B1/B2 are closed directly via this T9 plan. The tactical
workaround is not pursued. Detail is preserved in the prior version
of this plan (commit history) and in
[`review-cppm-config-template-findings.md`](./review-cppm-config-template-findings.md).

## Related Plans / Items

- [`research-block-registration-options.md`](./research-block-registration-options.md)
  — option-space evaluation and decision rationale.
- [`plan-development-ordering.md`](./plan-development-ordering.md) —
  T9 work item, dependencies on T6 and T7.
- [`review-cppm-config-template-findings.md`](./review-cppm-config-template-findings.md)
  — review items B1 and B2 are resolved by this plan.
- [`plan-cppm-module-scaffold-sections.md`](./plan-cppm-module-scaffold-sections.md)
  — `moduleScaffold` template precedent for adding a new
  single-purpose template; the block registrar support template
  follows the same shape for non-templated self-registration support.
- [`plan-parameterizable-config-template.md`](./plan-parameterizable-config-template.md)
  — defines the Config policy types whose stable tags are emitted by
  the trampoline.
