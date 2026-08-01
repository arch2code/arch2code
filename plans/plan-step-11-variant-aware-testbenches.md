# Plan: Step 11 - Minimal Variant-Selecting Testbenches

## Status

As of 2026-05-15:

- Overall status: complete on this branch, aligned with
  [`plan-variant-config-unification.md`](./plan-variant-config-unification.md)
  Stage 11. The implementation is recorded as implemented in working tree and
  verified for the maintained `examples/ip_test::ip` fixture; no committed
  status is claimed here.
- Step 11.1 - Step 11.4: complete from prior work on this branch. The
  generated artifacts for `examples/ip_test::ip` carry
  `// GENERATED_CODE_PARAM --block=ip --variant=variant0`, bind to
  `ipVariant0Config` consistently across `ipTestbench`, `ipExternal`,
  and `ipConfig`, and pass `"variant0"` to the DUT factory lookup. Not
  re-verified end-to-end in this round.
- Step 11.5: complete. `examples/ip_test/tb/ip/ipExternal.{h,cpp}` now
  registers an `SC_THREAD(stimulusThread)` that constructs an
  `ipDataSt<ipVariant0Config>` with `marker=1` and `data.word[1]=0x2A`
  (the values asserted in `ip::dataHandler`), pushes via
  `ipDataIf->push(data)`, then votes end-of-test through a private
  `endOfTest eot_{true}` member. `./build/run ip` ends with `No error`.
- Step 11.6: complete. `templates/systemc/module_hdl_wrapper.py` now
  emits a Config-templated wrapper (`template<typename DUT_T, typename
  Config>`) for every block that declares own `params:`. The
  `useOwnVariantConfig` path is gated on `isParameterizable and
  hasOwnParams`; it no longer falls back to project-wide
  `srcDefaultConfig` when port structs are Config-dependent. The base
  class inheritance, BFM declarations, hdl_if declarations,
  `SC_HAS_PROCESS` self-type alias, and `bfm_connect` references all
  thread `Config` through. Per-variant `using` typedefs bind
  `Config = <block><Variant>Config` (e.g. `ipVariant0Config`,
  `ipVariant1Config`, `srcVariantSrc0Config`,
  `ipLeafVariantLeaf0Config`). For blocks parameterizable only through
  contained children (e.g. `ip_top`), the wrapper stays non-templated
  on Config and omits the `<...>` suffix from the base class — fixing
  a pre-existing bug where `ip_topBase<srcDefaultConfig>` was emitted
  for a non-template `ip_topBase`.

  Verified end-to-end: `make -C examples/ip_test gen && make -C
  examples/ip_test/rundir all VL_DUT=1` builds clean, and
  `./build/run ip --vlInst tb.ip` drives the directed marker=1,
  data.word[1]=0x2A push through the Verilated `ip` DUT and ends with
  `No error`. `./build/run ip` (model path) and `./build/run ip_top`
  (container path) also pass with `No error`.

Incidental fixes landed alongside the 11.5 work:

- `examples/ip_test/tb/ip_top/ip_topExternal.{h,cpp}` switched
  `// GENERATED_CODE_PARAM --block=ip_top` to
  `--block=ip_top_tb --excludeInst=u_ip_top`, mirroring the working
  `mixedExternal` pattern. Before the change the generator populated
  `tb.external` with phantom duplicates of `ip_top`'s own children and
  never instantiated `uCPU`, which left no end-of-test voter and broke
  `./build/run ip_top`.
- `examples/ip_test/tb/ip_top/ip_topConfig.cpp::createTestBench` now
  calls `testController::set_test_names({...})` for the two cpu test
  names (`test_ip_uIp0_check`, `test_ip_uIp1_check`) so
  `cpu::checkUIp0`/`checkUIp1` can call `register_test_name` without
  exiting.
- `common/systemc/q_assert.cpp` gates every `wait()` and the `sc_stop()`
  call on a new `inThreadProcess()` helper. Asserts fired from
  `final()` (or any non-SC_THREAD context) no longer emit the follow-on
  `Error: (E519) wait() is only allowed in SC_THREADs and SC_CTHREADs`
  on top of the real failure.
- `examples/ip_test/verif/vl_wrap/ipLeaf_hdl_sc_wrapper.h` carried a
  stale `template <typename DUT_T>` line between two
  `GENERATED_CODE_BEGIN/END` blocks from an earlier generator pass.
  Removed during Step 11.6 because the current template emits the full
  class-template head inside the generated region.

## Purpose

This is the standalone plan for Step 11 of
[`plan-variant-config-unification.md`](./plan-variant-config-unification.md).
It converts the research in
[`research-variant-aware-testbench-use-cases.md`](./research-variant-aware-testbench-use-cases.md)
into the smallest useful implementation step.

The research shows that a fully general testbench-target model needs
more design: verification-only variants, per-instance DUT selection,
parameter sweeps, and shared typed testbenches all have different
contracts. Step 11 deliberately does not solve that full problem.

### Scope Boundaries

The following invariants apply to all sub-steps below.

- One testbench artifact and class family per block. For a block named
  `ip`, the generated files remain exactly `ipTestbench.*`,
  `ipExternal.*`, and `ipConfig.*`, regardless of how many DUT variants
  the block compiles.
- File-generation entries for the testbench, external, and config
  artifacts MUST NOT be flagged as variant-fanned. In project database
  terms, no `variant: true` (or equivalent multi-emission flag) is set
  on these TB file-generation entries. There is exactly one emission
  per artifact per block.
- `--variant` is solely a generated-code parameter. Templates consume
  it to select the DUT Config type and the factory variant string used
  inside the single emitted artifact. It does not multiply files,
  classes, or registrations.
- The file-level parameter form is:

  ```cpp
  // GENERATED_CODE_PARAM --block=ip --variant=variant0
  ```

  That `--variant` value is a generation-time selection. It chooses a
  Config type and factory key that already exist in the project
  database; it does not create a new parameterization and it is not a
  runtime test knob. A later stage may introduce a richer YAML contract
  for verification targets or reusable multi-variant testbenches.

## Problem Statement

- For a block with own `params:` and named variants, generated
  `tb/<block>/<block>Testbench.*`, `<block>External.*`, and
  `<block>Config.*` files must bind the same concrete Config policy and
  variant string as any other DUT construction site.
- Today the generated testbench skeletons carry only
  `GENERATED_CODE_PARAM --block=<block>`. For a parameterized DUT that
  makes `templates/systemc/testbench.py` fall back to
  `<context>DefaultConfig` and an empty factory variant string. That is
  wrong for `examples/ip_test` leaf variants such as `ip::variant0` /
  `ipVariant0Config` and `ip::variant1` / `ipVariant1Config`.
- Top-level/container testbenches such as `examples/ip_test::ip_top`
  remain architecture-faithful. Their child variants still come from
  YAML instance bindings (`uIp0`, `uIp1`, `uSrc`, etc.). They do not need
  a new `--variant` unless the container block itself declares own
  `params:`.
- The same variant-selection issue exists in the generated Verilated
  SC wrapper path. The full `make -C examples/ip_test VL_DUT=1` path
  remains part of this step until `module_hdl_wrapper.py` binds wrapper
  class bodies, BFM types, and factory registrations to concrete
  per-variant Configs instead of `defaultConfig` / worst-case BFM sizing.

## Planned Work

### Step 11.1 - Parse And Validate `--variant`

Reuse the existing `GENERATED_CODE_PARAM --variant` syntax for generated
testbench files.

When the DUT block has own `params:` and multiple named variants, require
`args.variant` for standalone `testbench`, `tbExternal`, and `tbConfig`
generation. The diagnostic should name the DUT block, list available
generated variants, and tell the user to add file-level `--variant`.

For a block with no own params, keep the current empty Config/variant
behavior.

### Step 11.2 - Resolve One Selected DUT Config

Add a small testbench-facing helper, preferably near the existing Config
view logic rather than inside Jinja templates, that maps
`(qualBlock, variant)` to:

- the selected Config name,
- the context Config header that defines it,
- the factory variant string.

Do not add a schema field or infer verification-only variants in this
step.

### Step 11.3 - Thread The Config Through `testbench.py`

Update `templates/systemc/testbench.py` so standalone
leaf-parameterizable DUT companions use the selected Config for:

- `tb_sec_header`,
- `tb_sec_init`,
- `ext_sec_header`,
- `ext_sec_init`,
- `tb_config_class`.

The selected Config must drive `Channels`, `Inverted`, `Base`, shared
pointer casts, and any generated local channel type substitutions. The
DUT `createInstance(...)` call must pass the selected variant string
rather than `""`.

### Step 11.4 - Thread `--variant` Through TB Skeleton Creation

Update the `make newmodule` / `templates/fileGen/fileGen.py` testbench
skeleton path so the single emitted TB skeleton for a parameterized
block carries `GENERATED_CODE_PARAM --block=<block> --variant=<variant>`
in the testbench, external, and config files.

Skeleton creation does not take a global variant argument. When a block
has multiple DUT variants, seed each generated TB artifact with the
first variant in that block's declaration order. That default is only a
starting point for the generated file: if a specific standalone TB should
target a different DUT variant, the user edits the file-level
`GENERATED_CODE_PARAM --variant=...` in that TB family and reruns
generation.

Constraints for this sub-step:

- Do not introduce variant-suffixed file names or variant-suffixed
  class names. The artifacts remain `<block>Testbench.*`,
  `<block>External.*`, and `<block>Config.*` with their existing class
  family.
- Do not set `variant: true` (or an equivalent fan-out flag) on any TB
  file-generation entry in the project database. Each artifact is
  emitted exactly once per block.
- `--variant` is written into the generated-code parameter line of the
  single emitted artifact only; templates use it to select the DUT
  Config and factory variant string.

Keep the existing `--block`-only skeleton for non-parameterized blocks
and architecture-level containers.

### Step 11.5 - Build The `ip_test` Standalone Functional TB

Create a simple standalone testbench for a concrete `ip` variant under
`examples/ip_test/tb/` using the normal `hasTb` / `make newmodule` /
`make gen` flow.

The maintained regression should be functional, not compile-only. It
should instantiate the selected `ip` variant, drive a small directed
push_ack transaction, and assert the expected payload or handshake result.
This replaces `examples/mixed::blockF` as the maintained Step 11 repro.

### Step 11.6 - Cover The RTL Path For The Same Variant

Update `templates/systemc/module_hdl_wrapper.py` so generated
`*_hdl_sc_wrapper.h` aliases, class bodies, BFM declarations, and factory
registrations bind to the same selected per-variant Config as the
SystemC standalone testbench.

Validate with the matching `examples/ip_test` RTL run (`VL_DUT=1`) so
the Verilated DUT executes the same directed test, or so any remaining
failure occurs after successful linkage of the wrapper for the selected
variant and DUT instantiation.

## Acceptance Criteria

- For `examples/ip_test::ip`, exactly one set of TB artifacts exists:
  `ipTestbench.*`, `ipExternal.*`, and `ipConfig.*`. No variant-suffixed
  testbench files or classes are emitted.
- The project database carries no `variant: true` (or equivalent
  multi-emission flag) on testbench, external, or config file-generation
  entries.
- The generated standalone SystemC TB for `examples/ip_test::ip`
  includes `--variant=<variant>` in its generated-code parameters,
  references the matching `ip<Variant>Config` type, and passes the same
  variant string into the DUT factory lookup.
- The generated External and Config companions agree with the Testbench
  on the selected Config and include the context Config header that
  defines it.
- Running the standalone `ip_test` SystemC TB executes a directed
  functional check for the selected variant.
- Running the same `ip_test` TB with the RTL/Verilated DUT path builds
  the selected wrapper variant and executes the same functional check.

## Verification

Use the `examples/ip_test` project as the maintained fixture.

Expected checks:

```bash
make -C examples/ip_test gen
make -C examples/ip_test/rundir
make -C examples/ip_test VL_DUT=1
```

The standalone TB should fail the regression if the selected Config
type, factory variant string, SystemC DUT construction, or RTL wrapper
construction drift apart.
