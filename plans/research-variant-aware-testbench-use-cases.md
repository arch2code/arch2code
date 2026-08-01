# Research: Variant-Aware Testbench Use Cases

## Purpose

Stage 11 of `plan-variant-config-unification.md` currently identifies a
specific generator defect: a generated `hasTb: true` harness for a block
with its own `params:` can still bind the DUT through
`<context>DefaultConfig` and an empty factory variant string. That is a
real implementation bug, but the correct fix depends on what kind of
verification harness is being generated.

This note records the verification use cases that should inform the
Stage 11 contract. It is intentionally pre-decision: it describes the
problem space, constraints, and open questions, but does not choose the
YAML or generator contract.

## Current Generator Behavior

The maintained generated block-level testbench path is:

1. A block sets `hasTb: true` in YAML.
2. `make newmodule` creates files under `tb/<block>/`.
3. `make gen` fills generated regions through
   `templates/systemc/testbench.py`.

The generated harness is split into:

- `<block>Testbench.*`, which instantiates the DUT and the External.
- `<block>External.*`, which provides the surrounding verification
  environment.
- `<block>Config.*`, which registers the testbench with
  `testBenchConfigFactory` and creates the testbench instance.

For container-style testbenches, the External path already has useful
machinery. A file-level `GENERATED_CODE_PARAM --block=<tb_block>
--excludeInst=<dut_instance>` lets the generator identify the DUT
instance inside a `_tb` wrapper and move the remaining test environment
into the External module. Child instances inside the generated External
use their YAML `variant:` fields and per-variant Config types.

The Stage 11 gap is narrower: the generated Testbench side still treats
the DUT itself as if a single default Config were sufficient. For a
parameterized leaf block with named variants, the current template
derives `cfg` from `defaultConfig` and emits the DUT factory lookup with
an empty variant string. For `examples/mixed::blockF`, that means the
generated skeleton would try to build `blockFBase<mixedDefaultConfig>`
and call `instanceFactory::createInstance(..., "blockF", "")`, even
though the valid DUT registrations are `variant0` /
`blockFVariant0Config` and `variant1` / `blockFVariant1Config`.

The same issue appears in the Verilated SC wrapper path when wrapper
class bodies, BFM declarations, and registrations bind to a block-level
default or worst-case shape instead of the selected per-variant Config.

## Existing Mechanisms

### YAML Architecture

The existing schema already has these relevant concepts:

- `blocks.<block>.hasTb`: asks the generator to create a maintained
  generated testbench skeleton for the block.
- `blocks.<block>.params`: declares block parameters that become
  Config fields under the variant-as-Config model.
- `instances.<instance>.variant`: selects the variant used by a concrete
  architectural instance.
- `parameters.<block>` rows: bind `(block, variant, param)` to concrete
  values.

There is no separate schema field today that means "the generated
testbench DUT uses variant X."

### Variant-as-Config Model

Earlier stages adopted the rule that variant and Config are a single
selection dimension:

- Factory lookup uses `(blockType, variant)`.
- A named variant maps to a concrete C++ Config type such as
  `ipVariant0Config`.
- An anonymous single variant uses the empty variant string and a Config
  name such as `ipConfig`.
- Parent containers type each child member from the child instance's
  selected variant.

This model is compile-time oriented. Any command-line option that
selects a variant at runtime can only select among variants whose Config
types, wrappers, and registrations were already generated and linked.

### Instance-Bound Code Generation

Current per-variant Config descriptor generation is driven by variants
that are used by instances of the block, not merely by every variant
name listed in `parameters:`. This is a good fit for architecture-bound
top-level integration tests, but it matters for IP verification:
declaring many parameter rows is not enough to create many compiled
variants unless the project also binds those variants through instances
or another future code-generation contract.

### Testbench Configuration

The generated `*Config.cpp` path registers a testbench name with
`testBenchConfigFactory` and creates the testbench through
`instanceFactory`. Today that creation path uses the testbench block
name and an empty variant string. The existing mechanism selects a test
configuration, not a parameter variant for the DUT.

### Verilated and Tandem Selection

Existing make/run flows can choose a Verilated instance path, for
example through `--vlInst`, but that is not the same as creating a new
parameterization. The selected Verilated wrapper must already exist, be
compiled, and be registered under the corresponding variant.

## Verification Use Cases

### 1. Top-Level System Testbench

A top-level or subsystem testbench usually wants to verify the design as
integrated. The variants are already architectural facts: each instance
in the YAML hierarchy names the Config it uses.

`examples/ip_test::ip_top` is the representative shape. The top-level
container has `hasTb: true`, while instances such as `uIp0`, `uIp1`,
and `uSrc` carry concrete variant bindings. The generated top-level
testbench should not randomly choose a different parameterization for
those children, because the point of the test is the integrated design
configuration.

Requirements for this use case:

- Preserve the instance-level variants declared in YAML.
- Let the DUT be the whole top-level container when there is no
  `--excludeInst`.
- When a `_tb` wrapper and `--excludeInst` identify a DUT instance, the
  DUT variant should come from that excluded instance if it has one.
- Do not introduce command-line variant overrides that silently change
  the architecture under test.

### 2. Deterministic Block or IP Variant Testbench

A lower-level generated testbench for a leaf IP often wants to verify one
specific parameterization at a time. For example, a `blockF` testbench
might target `variant0` in one regression and `variant1` in another.

This is the immediate Stage 11 repro. The generator needs to know which
`blockF` variant the generated `blockFTestbench` is for, because that
choice affects C++ types, headers, factory lookup, Verilated wrapper
selection, and BFM types.

Requirements for this use case:

- The selected DUT variant must be explicit when multiple named variants
  exist.
- The generated Testbench and External files must use the same selected
  Config type.
- The DUT factory call must pass the selected variant string.
- Diagnostics should name the DUT block, list available generated
  variants, and tell the user where to make the selection.

### 3. One Testbench Running Many Compiled Variants

IP teams often want a common stimulus and scoreboard environment reused
across a set of legal parameterizations. This could mean building one
binary that can instantiate any of several already-compiled variants, or
building several binaries from the same source skeleton.

This use case is different from a top-level system test. The variants
are verification targets, not necessarily all used in the product
hierarchy.

Requirements for this use case:

- The generation contract must say how verification-only variants become
  compiled Config types if they are not otherwise instance-bound.
- Shared testbench source should avoid duplicating hand-written stimulus
  for each variant.
- Any runtime variant selector can only choose among variants that were
  generated and linked.
- The selected variant may affect interface widths and BFM types, so the
  design may need one typed testbench instantiation per variant even when
  the test sequence is shared.

### 4. Parameter Sweep Regression

A sweep regression tries many parameter combinations. In this codebase,
variants are currently named parameter sets in YAML, not a general
runtime parameter grid.

The practical sweep model today is therefore to materialize variants
ahead of time, regenerate, build, and run the resulting compiled
variants. A future helper could generate those YAML variants or invoke
make targets repeatedly, but Stage 11 should not assume arbitrary new
parameter values can be supplied after compilation.

Requirements for this use case:

- Sweep values must be materialized before code generation.
- Generated variants need stable names so failures are reproducible.
- Cross-interface compatibility, address sizing, and Verilated wrapper
  emission must run for every selected variant.
- Build orchestration should be outside the hand-written test sequence
  where possible.

### 5. Randomized Parameter Exploration

Randomizing block parameters is useful for IP robustness testing, but
hardware parameterization is usually an elaboration-time concern. Widths,
array sizes, memory depths, generated structs, RTL parameters, BFM
types, and wrapper classes are all affected by the chosen values.

That means parameter randomization cannot be treated like ordinary
runtime stimulus randomization. The randomized values must either:

- be promoted into generated named variants before build, or
- be limited to runtime knobs that do not affect generated types,
  interfaces, memory layout, or RTL parameters.

Requirements for this use case:

- Separate compile-time parameters from runtime test controls.
- Record randomized compile-time parameter sets as named variants so a
  failing run can be reproduced.
- Avoid silently creating invalid cross-interface combinations.
- Keep runtime stimulus randomization in the testbench or
  `testBenchConfigFactory`; keep structural parameter randomization in
  pre-generation orchestration.

### 6. Verilated or Tandem Block Testbench

When the DUT is replaced by a Verilated wrapper or used in tandem, the
wrapper must represent the same variant as the SystemC model side of the
testbench. A mismatch in Config type, BFM width, or factory variant key
can fail at compile/link time or produce a misleading comparison.

Requirements for this use case:

- Wrapper aliases and class bodies must bind to the selected per-variant
  Config.
- Factory registration must preserve the same `(blockType, variant)`
  key shape as the model path.
- `--vlInst` or similar runtime selection should select an already-built
  instance/wrapper, not invent a new parameterization.
- Model/model, RTL/model, and wrapper-only tests should share the same
  variant naming convention.

### 7. Single-Variant and Anonymous-Variant Blocks

Some blocks have no named variants, or only one legal variant. These
cases should stay simple.

Requirements for this use case:

- A block with only the anonymous variant can continue using the empty
  variant string.
- A block with exactly one named variant can be a candidate for implicit
  selection, but the generated artifact should still make the selected
  variant visible.
- The single-variant convenience must not mask the multi-variant case.

## Requirement Themes

### Compile-Time Selection Versus Runtime Selection

Parameterized hardware shapes are elaboration-time artifacts. A runtime
option can choose among linked variants, but it cannot create a new
`Config` type, resize a BFM, regenerate an RTL wrapper, or change a
compiled structure layout.

Stage 11 should therefore treat variant selection as a generation/build
contract first. Runtime selection can be layered on only when the set of
compiled variants is already known.

### Architectural Variants Versus Verification Variants

Top-level tests should follow the architecture's instance variants.
Lower-level IP verification may need variants that are not otherwise
present in the product instance tree.

The current generator mostly understands architectural instance-bound
variants. A future lower-level verification contract may need a way to
mark additional variants as verification targets without pretending they
are product instances.

### DUT Instance Selection Versus DUT Variant Selection

`--excludeInst` answers "which instance inside this `_tb` wrapper is the
DUT?" It does not by itself answer "which variant should a direct leaf
block testbench instantiate?" unless that excluded instance carries a
variant in YAML.

For direct `hasTb: true` leaf tests, the generator needs either an
explicit DUT variant setting or a deterministic rule for the single
available variant case.

### Test Configuration Versus Design Configuration

`testBenchConfigFactory` is the right home for test controls: number of
transactions, seeds, timeouts, directed scenario names, and similar
runtime choices.

Design parameters that affect generated code should remain in YAML
variants and Config policies. Mixing these two concepts would make
failures harder to reproduce and could imply runtime flexibility that
compiled SystemC/RTL does not have.

### Diagnostics

The generator should avoid silent selection whenever more than one
variant is plausible. Clear diagnostics should include:

- the DUT block name,
- the variants available for that block,
- whether those variants are instance-bound or only declared,
- the field or file-level parameter the user should set.

## Open Questions for a Later Stage 11 Contract

- Should direct `hasTb: true` leaf testbenches select a DUT variant
  through a new block-level YAML field, a generated-code parameter such
  as `--variant`, or a generated `_tb` wrapper instance with
  `variant:`?
- Should verification-only variants be represented as ordinary YAML
  instances, a new list of testbench targets, or external regression
  orchestration that rewrites/generates YAML?
- Should a generated testbench produce one typed harness per selected
  variant, one runtime-selectable harness over precompiled variants, or
  both?
- Should `make newmodule` scaffold `--excludeInst` for `_tb` wrapper
  testbenches so the generated skeleton matches the documented pattern?
- How should `testBenchConfigFactory` expose runtime test controls
  without implying that structural DUT parameters can be changed at
  runtime?
- What is the intended lifecycle for randomized parameter exploration:
  checked-in named variants, generated temporary variants, or an
  external sweep runner?
- Should Verilated wrapper generation consume exactly the same selected
  variant set as generated SystemC testbenches, or does it need a
  separate wrapper-target list?
  - **Partial answer (2026-07-17), cross-level case:** neither an instance
    set nor a separate target list — the **immediate ASSEMBLING project owns
    and emits each concrete foreign-variant wrapper** for a variant it both
    declares and instantiates. Distinct assembler `projectName`s each own their
    Config/wrapper/registration, even for the same local variant name. This is
    the wrapper-ownership rule; it does not by itself choose the enumeration
    for a single-project testbench target list. P1's SC-path Config blocker is
    resolved by the landed S3-H (composed `ip_test` clean rebuild builds/runs
    No error); P3's contract is settled and P2 remains
    gated on Q-C8/C2/M-split/registrar completion; see
    [`plan-cross-level-variant-wrappers.md`](./plan-cross-level-variant-wrappers.md).

## Preliminary Non-Decisions

This research suggests several constraints but deliberately stops short
of choosing a fix:

- Top-level generated testbenches should be architecture-faithful.
- Lower-level IP testbenches need an explicit way to name or enumerate
  DUT parameterizations.
- Runtime test options should not be treated as compile-time hardware
  parameter overrides.
- Stage 11 should diagnose ambiguous multi-variant DUT generation before
  editing templates to choose a default.

The next step is to convert these use cases into a Stage 11 contract and
then update `plan-variant-config-unification.md` with the selected
direction.
