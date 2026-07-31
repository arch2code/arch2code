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

1.  Declare a block's root parameters — the constants named in `params:` and bound per variant — in `ipParameters` in the block's own YAML file. Types and derived constants that only *reference* those parameters are parameterizable wherever they are declared and may stay in the regular `types:`/`constants:` sections; they do not have to be moved into `ipParameters`.
2.  List the block parameters in the block's `params:` field.
3.  Bind concrete values in the top-level `parameters:` dictionary by block and variant.
4.  Use `maxValue` / `maxBitwidth` to describe the largest supported generated shape.
5.  Use explicit `ports:` on parameterizable blocks so the block owns its port shape.
6.  Do not write generated metadata such as `isParameterizable`, structure `maxBitwidth`, or register `maxBytes`.

## `ipParameters`

Use `ipParameters` for the block's **root parameter constants** — the variant knobs listed in `params:` and bound per variant in the top-level `parameters:` dictionary. These must live in `ipParameters` in the block's own (IP-root) YAML file, because that is how the generator identifies them as the variant-bound parameters.

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

Instead of selecting a variant, a contained instance may inherit its container's active config with `inheritContainerParam:` — see [Container Config Inheritance](#container-config-inheritance-inheritcontainerparam).

## Emitted Config

A block with `ipParameters` always emits configuration types: a `<block>DefaultConfig` plus one `<block><Variant>Config` per variant, with no folding of common values. The block class is templated on that Config (`template<typename Config> ... <block>Base<Config>`), and each instance's variant selects which `<block><Variant>Config` binds the class.

## Container Config Inheritance (`inheritContainerParam`)

A contained instance may set `inheritContainerParam: true` **in place of** `variant:`. That instance is then typed with the **container** block's active `Config` template symbol rather than with one of the child's own `<block><Variant>Config` structs. Because a contained child renders inside the container's templated class scope, C++ template instantiation resolves the concrete struct — including the container's own variant, transitively — at the container's instantiation site; no config value is plumbed. The child block still keeps its own `params:` and still emits its own `<block>DefaultConfig` for standalone use.

Use this when **two sibling contained blocks share one config context** and must bind a `Config`-parameterized channel payload between them (e.g. `bayer_preprocess_stream_t<Config>`). Without inheritance each sibling is typed with its own distinct block-named config struct (`preprocessDefaultConfig` vs `interpolateDefaultConfig`) — byte-identical but distinct C++ types — so no single `Config` satisfies both the producer and consumer ports and the channel cannot bind. Typing both siblings on the container's `Config` unifies them.

```yaml
instances:
  u_preprocess:  {container: debayer, instanceType: preprocess,  inheritContainerParam: true}
  u_interpolate: {container: debayer, instanceType: interpolate, inheritContainerParam: true}
```

Preconditions (all `make db`-time errors):

*   The child's `params:` must be a by-**name** subset of the container's params.
*   `inheritContainerParam:` is mutually exclusive with `variant:` on one instance.
*   The container block must be parameterized (declare `params:`).
*   The child block must declare `params:`.
*   Container and child must be the **same owning project** (no cross-project inheritance for now).
*   The instance must be contained in a block (not the root top instance).

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

When a parameterized producer interface connects to a consumer interface with a different interface name, both sides must be structurally compatible:

*   Same interface meta-protocol.
*   Same structure list and structureType ordering.
*   Same field names and field ordering.
*   Exact active field-width agreement under the bound variants.
*   Matching active packed bit positions.

Keep cross-parameter binds on the consumer's destination side. Producer-side cross-interface binding is not a supported authoring shape.

Templated and untemplated structures may be compatible at the active packed-bit
level while remaining incompatible C++ types. The generated thunker is the
explicit bridge for those cases; see `STRUCTURES_AND_DATA_TYPES_REFERENCE.md`.

## Registers and Memories

Registers and memories may reference parameterizable structures or word counts. Address allocation uses worst-case sizing from `maxValue`, `maxBitwidth`, or the maximum variant-bound value.

```yaml
memories:
  - memory: data_mem
    block: ip
    structure: ip_data_st
    addressStruct: ip_addr_st
    wordLines: IP_MEM_DEPTH
    desc: "Parameterized memory"
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
