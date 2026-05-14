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

1.  Put variable constants and types in `ipParameters` in the block's own YAML file.
2.  List the block parameters in the block's `params:` field.
3.  Bind concrete values in the top-level `parameters:` dictionary by block and variant.
4.  Use `maxValue` / `maxBitwidth` to describe the largest supported generated shape.
5.  Use explicit `ports:` on parameterizable blocks so the block owns its port shape.
6.  Do not write generated metadata such as `isParameterizable`, structure `maxBitwidth`, or register `maxBytes`.

## `ipParameters`

Use `ipParameters` for constants and types that vary by instance or variant. Entries follow the normal `constants` and `types` schemas, then become parameterizable.

```yaml
ipParameters:
  constants:
    IP_DATA_WIDTH: {value: 8, maxValue: 16, desc: "Per-instance data width"}
    IP_MEM_DEPTH: {value: 16, maxValue: 32, desc: "Per-instance memory depth"}
    IP_DATA_WIDTH_X2: {eval: "$IP_DATA_WIDTH * 2", desc: "Derived width"}
  types:
    ip_data_t: {width: IP_DATA_WIDTH, desc: "IP data word"}
```

Rules:

*   Direct parameterizable constants require `maxValue`.
*   Direct literal-width parameterizable types require `maxBitwidth`.
*   Derived constants and types inherit worst-case bounds from referenced parameterizable constants.
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

Concrete values are bound in the top-level `parameters:` dictionary. Each list entry names a `variant`, a `param`, and a `value`.

```yaml
parameters:
  ip:
    - {variant: variant0, param: IP_DATA_WIDTH, value: 8}
    - {variant: variant0, param: IP_MEM_DEPTH, value: 16}
    - {variant: variant1, param: IP_DATA_WIDTH, value: 12}
    - {variant: variant1, param: IP_MEM_DEPTH, value: 8}
```

Instances select variants with `variant:`.

```yaml
instances:
  uIp0: {container: top, instanceType: ip, variant: variant0}
  uIp1: {container: top, instanceType: ip, variant: variant1}
```

Every variant should bind at least one parameter. Avoid label-only variants unless the generator flow explicitly requires them.

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
    - {variant: src_variant0, param: OUT0_DATA_WIDTH, value: 8}
    - {variant: src_variant0, param: OUT1_DATA_WIDTH, value: 12}
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
