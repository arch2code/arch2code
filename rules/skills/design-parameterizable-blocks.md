---
name: design-parameterizable-blocks
description: Guide for defining parameterizable arch2code YAML blocks, variants, ipParameters, explicit ports, parameter bindings, and per-port parameters. Use when authoring blocks whose widths, depths, structures, registers, memories, or interfaces vary by instance.
---
# Skill: Design parameterizable blocks

## Purpose
Define parameterizable arch2code blocks in YAML. Use this skill when a block has per-instance widths, depths, structure shapes, register or memory sizing, or several variants.

For regular block hierarchy and wiring, use `design-architecture.md`. For base constant, type and structure syntax, use `design-types-structures.md`. For generated structure representation, active and worst-case packed forms, and thunker behavior, use `STRUCTURES_AND_DATA_TYPES_REFERENCE.md`.

## Core rules

1.  Declare each root parameter, a constant named in a block's `params:` and bound per variant, under `ipParameters:`.
2.  List the block parameters in the block's `params:` field.
3.  Bind concrete values in the top-level `parameters:` dictionary by block and variant.
4.  Use `maxValue` / `maxBitwidth` to describe the largest supported generated shape.
5.  Declare explicit `ports:` on a reusable-IP boundary block so the block owns its port shape. A self-contained block infers its ports top-down from its container and declares none.
6.  Do not write generated metadata such as `isParameterizable`, structure `maxBitwidth`, or register `maxBytes`.

## `ipParameters`

Each name in `params:` must resolve to exactly one plain constant, declared without `eval`, that is parameterizable. `make db` rejects a name visible more than once or not at all, and a backing constant that is not parameterizable or uses `eval`. Declaring the constant under `ipParameters:` makes it parameterizable and requires its `maxValue`.

The declaring file can be any file the block's file sees through `include:`. That may be the block's own file, or a definitions-only file with no `blocks:` that several IPs include. A file with no regular `types:`, `enums:`, `constants:` or `structures:` entry gets no context module or package. A type it declares under `ipParameters:` then has no model declaration, because the model's `<type>_v` template is emitted only into that context module. The RTL is unaffected, since each block declares the type module-local. Give that file at least one regular entry, as `examples/xprojParam/cstShared/yaml/xpCstSharedDefs.yaml` does.

```yaml
ipParameters:
  constants:
    IP_DATA_WIDTH: {value: 8, maxValue: 16, desc: "Per-instance data width"}
    IP_MEM_DEPTH: {value: 16, maxValue: 32, desc: "Per-instance memory depth"}
    IP_DATA_WIDTH_X2: {eval: "$IP_DATA_WIDTH * 2", desc: "Derived width"}
  types:
    ip_data_t: {width: IP_DATA_WIDTH, desc: "IP data word"}
```

Types and derived constants that reference a root parameter are parameterizable wherever they are declared. They generate the same in `ipParameters:` or in the regular `types:`/`constants:` sections, so putting them in `ipParameters:` only keeps them next to the parameter. Moving a file's last regular entry into `ipParameters:` removes its context module, and with it the model declaration of its `ipParameters:` types, as described above.

Rules:

*   A literal constant declared under `ipParameters:` requires `maxValue`.
*   A type declared under `ipParameters:` with a literal width requires `maxBitwidth`.
*   A derived constant takes its `maxValue` from its `eval`, and `make db` rejects one written by hand.
*   A type whose width names a parameterizable constant derives its bound and needs no `maxBitwidth`. With `width:` the bound is the constant's `maxValue`. With `widthLog2:` it is the bit length of `maxValue`, and with `widthLog2minus1:` the bit length of `maxValue - 1`.

A derived constant is generated as an expression over the block's parameters, so each variant computes its own value. SystemVerilog declares it as a `localparam` inside the modules of each block whose `params:` include every root parameter it uses, and the context package leaves it out. C++ declares it as a `static constexpr auto` in the block's Base class, written with `Config::<param>`, and expands it inline everywhere else; a `Config` struct carries only root parameters. A firmware header has no variants, so it emits a flat constant computed from the root parameters' default values. See `builder/base/specs/spec-eval-expressions.md`, section 6.

## Parameterized structures

Structures become parameterizable when they reference parameterizable types, sub-structures, or array sizes. Write the structure as usual. The generator derives its metadata.

```yaml
structures:
  ip_data_st:
    data: {varType: ip_data_t, desc: "Parameterized payload"}
  ip_burst_st:
    samples: {varType: ip_data_t, arraySize: IP_MEM_DEPTH, desc: "Parameterized burst"}
```

For parameterizable structures, address allocation and generated packed forms use the declared worst-case bounds.

## Block declaration

A parameterizable block names its parameters with `params:`. A reusable-IP boundary block, such as `ip` below, also declares `ports:` so its reusable YAML carries its external contract. A self-contained block declares no `ports:` (Core rule 5).

```yaml
blocks:
  ip:
    desc: "Parameterized IP"
    params: [IP_DATA_WIDTH, IP_MEM_DEPTH]
    hasVl: true
    ports:
      ipDataIf: {interface: ip_data_if, direction: dst}
```

The `ports:` map is keyed by port name. Each entry has:

*   `interface`: Interface name visible in the block's YAML context.
*   `direction`: `src` or `dst`, from the block's point of view.

## Variant bindings

Concrete values are bound in the top-level `parameters:` dictionary, keyed by block and then by variant. Each variant maps its parameter names to values.

```yaml
parameters:
  ip:
    variant0:
      IP_DATA_WIDTH: 8
      IP_MEM_DEPTH: 16
    variant1:
      IP_DATA_WIDTH: 12
      IP_MEM_DEPTH: 8
```

Each binding takes one of these forms:

| Written as | Meaning |
| :-- | :-- |
| `PARAM: 5` | the literal 5 |
| `PARAM: OTHER_CONST` | the value of a constant visible in scope |
| `PARAM: { value: 5 }` | the literal 5, long form |
| `PARAM: { containerParam: OTHER }` | the containing block's parameter `OTHER` |

`make db` rejects `PARAM: {}`, which binds nothing, and a binding that gives both `value:` and `containerParam:`.

A project declares each variant of a block once. `make db` rejects a second declaration of the same `(block, variant)` in another file of the same project, even where no single file sees both.

Instances select variants with `variant:`.

```yaml
instances:
  uIp0: {container: soc, instanceType: ip, variant: variant0}
  uIp1: {container: soc, instanceType: ip, variant: variant1}
```

Every variant must bind all of the block's declared `params:`. An omitted parameter has no default. A variant that binds nothing is rejected, whether or not the block declares `params:`.

When a block takes its Config from more than one source, itself and a container whose Config it inherits, a label declared by two of those sources is rejected, because it would name two Configs of the block.

A named variant resolves through the file holding the instance row, the files it includes, and the files those include. Exactly one of those files must declare the label. `make db` rejects zero visible declarations or more than one. The error names every declaring file it can see, or the files that declare the label out of scope. For a block that declares no `params:`, it names the block instead. Two projects may each declare the same label for a block they both reach. Each is a separate declaration, and a consumer resolves to the one its own scope reaches.

A contained instance can also take parameter values from its container. Write `containerParam:` on a parameter in its variant's rows, or set `inheritContainerParam: true` in place of `variant:` to take every parameter. See [Container-sourced parameters](#container-sourced-parameters-containerparam-inheritcontainerparam).

Every instance of a params-declaring block must select a Config, and `make db` rejects one that does not. An instance selects a Config in one of three ways: a `variant:` binding values or constants, a `variant:` whose rows use `containerParam:`, or `inheritContainerParam: true`. Without one, the instance would have no type, and the model and RTL would disagree about its values.

A top instance's block may not declare `params:`, and `make db` rejects it. A top has no container, so neither container-sourcing form is available. A project declares one top, so a variant there could bind only one set of literals. Put an unparameterized block at the root and the parameterized block one level down.

```yaml
blocks:
  myRoot: {desc: "Unparameterized root"}
  myHarness:
    desc: "Parameterized, so it cannot be the top"
    params: [IP_DATA_WIDTH]

instances:
  myRoot:    {container: myRoot, instanceType: myRoot}
  uHarness:  {container: myRoot, instanceType: myHarness, variant: variant0}
```

## Emitted Config

A block that declares `params:` emits a `<project>_<block>DefaultConfig`, plus one `<project>_<block><Variant>Config` per variant. A variant named `default` that the block's owner declares is the default Config, so the block then emits one Config per variant and no extra default. Nothing folds common values across them. `<Variant>` is the variant label with its first letter capitalized. A block named `<project>` or `<project>_...` takes no extra prefix in its Config names or Config file. In `examples/ip_test`, block `ip` of project `ip` emits `ipDefaultConfig` and `ipVariant0Config`. In `examples/xprojParam/inhLayout`, project `xpInhLayout`, variant `use` of `xpInhWrap` gives `xpInhLayout_xpInhWrapUseConfig`.

`<project>` is the declaring project. For the default, and for any variant a block declares itself, that project is the block's own owner. For a variant another project declares of a reused block, `<project>` is that other project instead. The block's owner is the project that owns the file declaring the block, not the file declaring its `ipParameters`.

A project writes every Config it declares for one block, its own block or a reused one, into one module file under its `registrar/` directory, `<project>_<block>VariantConfig.cppm`. No other project's files carry that Config, and it has no unqualified spelling.

The block's model class `<block>` is a `template<typename Config>` class derived from `<block>Base<Config>`, as `examples/ip_test`'s `ip` shows. An instance's `variant:` selects which `<project>_<block><Variant>Config` binds it. An `inheritContainerParam: true` instance binds its container's Config instead. A block's own testbench selects its DUT Config with `--variant=` (`verify-testbench`, "DUT variant selection").

## Container-sourced parameters (`containerParam`, `inheritContainerParam`)

A parameter inside a variant can be sourced from a parameter of the block that contains the instance, instead of bound to a value. Write `containerParam:` on the child's parameter, naming the container's parameter.

```yaml
blocks:
  xpCpWrap:
    params: [CP_BUS_W]
  xpCpLeaf:
    params: [CP_WIDTH]

instances:
  uWrap: { container: xpCpLayoutTop, instanceType: xpCpWrap, instGroup: top, variant: use }
  uLeaf: { container: xpCpWrap,      instanceType: xpCpLeaf, instGroup: top, variant: use }

parameters:
  xpCpWrap:
    use:
      CP_BUS_W: 16
  xpCpLeaf:
    use:
      CP_WIDTH: { containerParam: CP_BUS_W }
```

The child's parameter and the container's do not need to share a name. Here the leaf's `CP_WIDTH` is sourced from the container's `CP_BUS_W`. They do not need to belong to the same project either. The container's parameter and the child's can be backed by different constants in different projects.

The generator checks only `maxValue`. The container's parameter may not accept a value larger than the child's, and the diagnostic names both constants and both bounds.

Inheritance is single level. `containerParam:` names a parameter of the immediate container. Naming one that only a block further up declares is rejected, and the message names that block. Declare the parameter on each level in between and source it level by level.

`inheritContainerParam: true` applies the same mechanism to every parameter at once, with the same names, the same project and no variant named.

```yaml
# examples/xprojParam/inhLayout/yaml/xpInhLayoutTop.yaml
instances:
  uLeafA: { container: xpInhWrap, instanceType: xpInhLeaf, instGroup: top, inheritContainerParam: true }
  uLeafB: { container: xpInhWrap, instanceType: xpInhLeaf, instGroup: top, inheritContainerParam: true }
```

Two sibling instances that bind a `Config`-templated channel between them must agree on the value of every parameter the payload uses. The generated payload type takes those values as template arguments, not the Config. For `xpInhLayoutTop.yaml`, `model/xpInhLayoutTopIncludes.cppm` declares `ilSt_v<IL_WIDTH>` and `template<typename Config> using ilSt = ilSt_v<Config::IL_WIDTH>;`. There `uSrc` binds `IL_WIDTH: 16` through variant `inner`, and `uLeafA` takes 16 from `xpInhWrap`. Both ends name `ilSt_v<16>`, so the channel binds them directly although their `Config` names differ. `make db` checks the values on each such interface, including across a container's `connectionMaps:` boundary (`uLeafB`), and rejects values that differ (`examples/xprojParam/inhLayoutBad`, `uLeafA`). `inheritContainerParam: true` is the simplest way to guarantee agreement, because both siblings take the container's values.

A register-bus router block, one with `addressBlock:`, may declare `params:` and inherit like any other block. The generator checks its junction with the parent router at the configuration the container binds.

The register bus itself stays fixed-width. `make db` rejects an `addressBus` interface that carries a parameterizable structure, so size a register's payload by a parameter, never the bus structure.

`make db` also rejects a `hasRtl: true` container that declares no `params:` but wires two children over a parameterizable interface. Its SystemVerilog module would name a struct type that no package declares. Give the container `params:` and inherit or bind the children, make the structure fixed-width, or drop `hasRtl`.

A block that declares `params:` but no `ports:` binds each inferred port to the channel directly, with no adapter. The same rule applies. The instance's Config must give the payload the same field widths as the channel, and equal values under different Config names are accepted. `make db` rejects a mismatch and names both sides. Inherit the container's configuration, or, for reusable IP, declare the port in `ports:` so an adapter is generated.

Use the shorthand only where its conditions hold, all checked at `make db`:

*   The child's `params:` must be a by-name subset of the container's.
*   Container and child must belong to the same project.
*   `inheritContainerParam:` is mutually exclusive with `variant:` on one instance.
*   The container block must declare `params:`, and so must the child.
*   The instance must be contained in a block, not the root top instance.
*   Each child parameter must be the container's own `ipParameters` constant. A same-named parameter backed by a different declaration is rejected. Use `containerParam:` for that case.

Outside those conditions, use `containerParam:` per parameter instead. The generator never compares `valueType`, so a signed container parameter sourced into an unsigned child parameter is accepted.

## Per-port parameters

When one producer block has multiple output ports that feed consumers with different parameter values, declare one parameter per output port instead of one shared output parameter.

```yaml
ipParameters:
  constants:
    OUT0_DATA_WIDTH: {value: 8,  maxValue: 16, desc: "Width for out0"}
    OUT1_DATA_WIDTH: {value: 12, maxValue: 16, desc: "Width for out1"}
  types:
    out0_data_t: {width: OUT0_DATA_WIDTH, desc: "Out0 data"}
    out1_data_t: {width: OUT1_DATA_WIDTH, desc: "Out1 data"}

structures:
  out0_data_st:
    data: {varType: out0_data_t, desc: "Out0 payload"}
  out1_data_st:
    data: {varType: out1_data_t, desc: "Out1 payload"}

interfaces:
  out0_if:
    interfaceType: rdy_vld
    desc: "Out0 stream"
    structures:
      - {structureType: data_t, structure: out0_data_st}
  out1_if:
    interfaceType: rdy_vld
    desc: "Out1 stream"
    structures:
      - {structureType: data_t, structure: out1_data_st}

blocks:
  src:
    desc: "Producer with independently sized outputs"
    params: [OUT0_DATA_WIDTH, OUT1_DATA_WIDTH]
    ports:
      out0: {interface: out0_if, direction: src}
      out1: {interface: out1_if, direction: src}
```

Bind both per-port parameters in the selected producer variant.

```yaml
parameters:
  src:
    src_variant0:
      OUT0_DATA_WIDTH: 8
      OUT1_DATA_WIDTH: 12
```

Use this pattern only when the output ports genuinely have different parameter values. If all consumers share the same shape, use one shared parameter.

## Cross-parameter connections

Wherever a connection interface meets a block's own declared port interface, both sides must be structurally compatible. This applies whether or not the two interfaces share a name: one interface declaration reached from two endpoints that bind different variants has two different payloads, and that case is checked too.

*   Same interface meta-protocol.
*   The same set of `structureType` entries. Each entry is paired with the other side's entry of the same `structureType`, whatever the list order.
*   Same field count, compared positionally.
*   Exact active field-width agreement under the bound variants.
*   Matching active packed bit positions.

Field names are not compared. Payloads are matched by position, because the generated thunker copies them by bit position, so a name difference cannot change generated behaviour. Names are printed in diagnostics for reference only. Two payloads with the same width profile but different meanings (`{r,g,b}` against `{y,u,v}`) are accepted and adapted, so keeping the channel order right is the author's responsibility.

A different field split at the same total width is not compatible. One side declaring a 32-bit field where the other declares two 16-bit fields has a different field count and is rejected.

Keep cross-parameter binds on the consumer's destination side. Producer-side cross-interface binding is not a supported authoring shape.

Templated and untemplated structures can match at the active packed-bit level and still be different C++ types. The generated thunker bridges them. See `STRUCTURES_AND_DATA_TYPES_REFERENCE.md`.

## Registers and memories

Registers and memories may reference parameterizable structures or word counts. Address allocation sizes them for the worst case: a parameterizable width from its `maxBitwidth`, and a parameterizable `wordLines` from the `maxValue` of its backing `ipParameters` constant. The variant bindings are never read for sizing. A binding larger than the backing constant's `maxValue` is rejected at `make db`, so raise `maxValue` to cover the largest variant.

```yaml
memories:
  - {memory: data_mem, block: ip, structure: ip_data_st, addressStruct: ip_addr_st, wordLines: IP_MEM_DEPTH, regAccess: rw, desc: "Parameterized memory"}
```

Only a register or a `regAccess` memory gets an address.

## Validation

Run `make db` after YAML edits.

Common errors:

*   Missing `maxValue` on direct parameterizable constants.
*   Missing `maxBitwidth` on literal-width parameterizable types.
*   Forgetting to list a parameter in the block's `params:`.
*   Binding a variant value that exceeds the backing constant's `maxValue`.
*   Cross-parameter connections whose payload fields do not match exactly.
*   `Parameterized interface '…' … which is not parameterized` (or `does not declare the required parameter(s)`). An endpoint block of a parameterized connection must declare every parameter the payload uses, because its module sizes the payload. Add the parameters to its `params:`, or declare the port with a different interface in `ports:` so an adapter is generated.
