---
name: design-parameterizable-blocks
description: Guide for defining parameterizable arch2code YAML blocks, variants, ipParameters, explicit ports, parameter bindings, and per-port parameters. Use when authoring blocks whose widths, depths, structures, registers, memories, or interfaces vary by instance.
---
# Skill: Design Parameterizable Blocks

## Purpose
Guide the user in defining parameterizable arch2code blocks in YAML. Use this skill when a block has per-instance widths, depths, structure shapes, register or memory sizing, or multiple variants.

For regular block hierarchy and wiring, use `design-architecture.md`. For base constant/type/structure syntax, use `design-types-structures.md`.
For generated structure representation, active vs. worst-case packed forms,
and thunker behavior, use `STRUCTURES_AND_DATA_TYPES_REFERENCE.md`.

## Core Rules

1.  Declare a block's root parameters, the constants named in `params:` and bound per variant, as an `ipParameters` constant, declared once in any file the block's file can see through `include:`, including a definitions-only shared file with no `blocks:` of its own. A name visible more than once, or not at all, is rejected. Types and derived constants that only *reference* those parameters are parameterizable wherever they are declared and may stay in the regular `types:`/`constants:` sections; they do not have to be moved into `ipParameters`.
2.  List the block parameters in the block's `params:` field.
3.  Bind concrete values in the top-level `parameters:` dictionary by block and variant.
4.  Use `maxValue` / `maxBitwidth` to describe the largest supported generated shape.
5.  Declare explicit `ports:` on a reusable-IP boundary block so the block owns its port shape. A self-contained block infers its ports top-down from its container and declares none.
6.  Do not write generated metadata such as `isParameterizable`, structure `maxBitwidth`, or register `maxBytes`.

## `ipParameters`

Use `ipParameters` for the block's **root parameter constants**: the variant knobs listed in `params:` and bound per variant in the top-level `parameters:` dictionary. These must live in `ipParameters`, declared once in any file reachable through the block's `include:` chain, because that is how the generator identifies them as the variant-bound parameters. The declaring file may be the block's own IP-root file or a definitions-only shared file with no `blocks:`, so several IPs can name one declaration.

```yaml
ipParameters:
  constants:
    IP_DATA_WIDTH: {value: 8, maxValue: 16, desc: "Per-instance data width"}
    IP_MEM_DEPTH: {value: 16, maxValue: 32, desc: "Per-instance memory depth"}
    IP_DATA_WIDTH_X2: {eval: "$IP_DATA_WIDTH * 2", desc: "Derived width"}
  types:
    ip_data_t: {width: IP_DATA_WIDTH, desc: "IP data word"}
```

Types and derived constants that reference these parameters do **not** have to be declared inside `ipParameters`. Parameterizability propagates from the referenced root parameter, so such entries generate identically whether they sit in `ipParameters.types`/`ipParameters.constants` or in the regular `types:`/`constants:` sections. Declaring them in `ipParameters` is a locality convention only. (For example, a `pixel_t` whose `width` is a parameter, and derived types such as accumulator or address types whose widths come from derived constants, are routinely declared in the regular `types:` section.)

Rules:

*   Direct parameterizable constants require `maxValue`.
*   Direct literal-width parameterizable types require `maxBitwidth`.
*   Derived constants and types inherit worst-case bounds from referenced parameterizable constants. A type whose width references a parameterizable constant inherits that constant's `maxValue` as its bound and needs no explicit `maxBitwidth`, in whichever section it is declared.
*   Do not put `ipParameters` in shared include files that only define common constants, types, or structures.

## Parameterized Structures

Structures become parameterizable when they reference parameterizable types, sub-structures, or array sizes. Keep the structure definition normal; the generator derives the metadata.

```yaml
structures:
  ip_data_st:
    data: {varType: ip_data_t, desc: "Parameterized payload"}
  ip_burst_st:
    samples: {varType: ip_data_t, arraySize: IP_MEM_DEPTH, desc: "Parameterized burst"}
```

For parameterizable structures, address allocation and generated packed forms use the declared worst-case bounds.

## Block Declaration

A parameterizable block names its parameters with `params:`. Prefer explicit `ports:` so the block's reusable YAML declares its external contract.

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

## Variant Bindings

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

Instances select variants with `variant:`.

```yaml
instances:
  uIp0: {container: top, instanceType: ip, variant: variant0}
  uIp1: {container: top, instanceType: ip, variant: variant1}
```

Every variant must bind **all** of the block's declared `params:` — there is no default-fill for an omitted parameter. Avoid label-only variants unless the generator flow explicitly requires them.

A named variant resolves through the file holding the instance row, the files it includes, and the files those include: one of those files must declare the label. Zero visible declarations or more than one is a `make db` error naming every declaring file it can see (or the file(s) that declare it out of scope), or naming the block itself when it declares no `params:` at all. Two projects may each declare one label for a block they both reach; each is its own declaration, and a consumer resolves to whichever one its own scope reaches.

Instead of selecting a variant, a contained instance may source its parameters from its container, either per parameter with `containerParam:` or, for every parameter at once, with `inheritContainerParam: true`. See [Container-sourced parameters](#container-sourced-parameters-containerparam-inheritcontainerparam).

**Every instance of a params-declaring block must select a Config, and `make db` rejects one that does not.** The legal shapes are the whole list: a `variant:` binding values or constants, a `variant:` whose rows use `containerParam:` to source from the container, or `inheritContainerParam: true`. An instance naming none of them leaves the block parameterized and the instance untyped, and the two languages then disagree about which values it carries.

**A top instance's block may not declare `params:`, and `make db` rejects it.** A top has no container, so neither container-sourcing form is available, and a project declares one top, so a variant could only ever bind one set of literals. Put an unparameterized block at the root and the parameterized block one level down.

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

A block with `ipParameters` always emits configuration types: a `<project>_<block>DefaultConfig`, plus one `<project>_<block><Variant>Config` per variant. Nothing folds common values across them.

`<project>` is the declaring project. For the default, and for any variant a block declares itself, that project is the block's own owner. For a variant another project declares of a reused block, `<project>` is that other project instead.

Every Config a project declares for one block, native or reused, lives in that project's own registrar-domain Config module (`<project>_<block>VariantConfig.cppm`). No other project's artefact carries it, and no bare, unqualified spelling exists.

The block class is templated on that Config (`template<typename Config> ... <block>Base<Config>`). Each instance's variant selects which `<project>_<block><Variant>Config` binds the class.

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

The child's parameter and the container's do not need to share a name. Here the leaf's `CP_WIDTH` is sourced from the container's `CP_BUS_W`. They do not need to belong to the same project either; the container's parameter and the child's can be backed by different constants in different projects.

The generator checks only `maxValue`: the container's parameter may not accept a value larger than the child's, and the diagnostic names both constants and both bounds.

`inheritContainerParam: true` is the same mechanism applied to every parameter at once: same names, same project, no variant named.

```yaml
instances:
  u_preprocess:  {container: debayer, instanceType: preprocess,  inheritContainerParam: true}
  u_interpolate: {container: debayer, instanceType: interpolate, inheritContainerParam: true}
```

Two sibling instances that bind a `Config`-templated channel between them need the same concrete `Config` type. Each on its own variant would carry a distinct `<project>_<block><Variant>Config`, and no single type would satisfy both ends. `inheritContainerParam: true` types both siblings on the container's `Config` instead.

A register-bus router block (one with `addressBlock:`) may declare `params:` and inherit like any other block; the generator checks its junction with the parent router at the configuration the container binds. The register bus itself stays fixed-width: `make db` rejects an `addressBus` interface that carries a parameterizable structure, so size a register's payload by a parameter, never the bus structure. `make db` also rejects a `hasRtl: true` container that declares no `params:` yet wires two children over a parameterizable interface, because its SystemVerilog module would name a struct type no package declares; give the container `params:` and inherit or bind the children, make the structure fixed-width, or drop `hasRtl`.

Use the shorthand only where its conditions hold, all checked at `make db`:

*   The child's `params:` must be a by-name subset of the container's.
*   Container and child must belong to the same project.
*   `inheritContainerParam:` is mutually exclusive with `variant:` on one instance.
*   The container block must declare `params:`, and so must the child.
*   The instance must be contained in a block, not the root top instance.
*   Each child parameter must be the container's own `ipParameters` constant. A same-named parameter backed by a different declaration is rejected; use `containerParam:` for that case.

Outside those conditions, use `containerParam:` per parameter instead. The compatibility check between a container's parameter and a child's covers only `maxValue`; the generator never compares `valueType`, so a signed container parameter sourced into an unsigned child parameter is accepted.

## Per-Port Parameters

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

## Cross-Parameter Connections

Wherever a connection interface meets a block's own declared port interface, both sides must be structurally compatible. This applies whether or not the two interfaces share a name: one interface declaration reached from two endpoints that bind different variants has two different payloads, and that case is checked too.

*   Same interface meta-protocol.
*   Same structure list and structureType ordering.
*   Same field count, compared positionally.
*   Exact active field-width agreement under the bound variants.
*   Matching active packed bit positions.

Field **names are not compared**. Payloads are matched by position, because the generated thunker copies them by bit position, so a name difference cannot change generated behaviour. Names are printed in diagnostics for reference only. A consequence worth knowing: two payloads with the same width profile but different meanings (`{r,g,b}` against `{y,u,v}`) are accepted and adapted, so keeping the channel order right is the author's responsibility.

A differing field *split* at the same total width is **not** compatible: one side declaring a 32-bit field where the other declares two 16-bit fields has a different field count and is rejected.

Keep cross-parameter binds on the consumer's destination side. Producer-side cross-interface binding is not a supported authoring shape.

Templated and untemplated structures may be compatible at the active packed-bit
level while remaining incompatible C++ types. The generated thunker is the
explicit bridge for those cases; see `STRUCTURES_AND_DATA_TYPES_REFERENCE.md`.

## Registers and Memories

Registers and memories may reference parameterizable structures or word counts. Address allocation uses worst-case sizing from `maxValue`, `maxBitwidth`, or the maximum variant-bound value.

```yaml
memories:
  - {memory: data_mem, block: ip, structure: ip_data_st, addressStruct: ip_addr_st, wordLines: IP_MEM_DEPTH, desc: "Parameterized memory"}
```

## Validation

Run `make db` after YAML edits.

Common errors:

*   Missing `maxValue` on direct parameterizable constants.
*   Missing `maxBitwidth` on literal-width parameterizable types.
*   Forgetting to list a parameter in the block's `params:`.
*   Binding a variant value that exceeds the declared worst-case bound.
*   Omitting explicit `ports:` on blocks whose port structures depend on parameters.
*   Cross-parameter connections whose payload fields do not match exactly.
