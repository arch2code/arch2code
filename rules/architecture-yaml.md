---
description: Architecture YAML conventions for defining hardware blocks, interfaces, connections, and types
globs: "arch/yaml/**/*.yaml"
alwaysApply: false
---
# Architecture YAML Rules

## Overview
YAML files in `arch/yaml/` define the hardware architecture. YAML is the **Single Source of Truth** - all implementation artifacts are generated from these definitions.

## Key Patterns

### Definition Order
Define elements in dependency order:
1. **Constants / ipParameters constants** - Parameters and sizing
2. **Types / ipParameters types** - Bit widths and enums
3. **Structures** - Data packets (use defined types)
4. **Interfaces** - Communication protocols (use defined structures)
5. **Blocks** - Reusable components
6. **Instances** - Block instantiations
7. **Connections** - Interface wiring

### Essential Syntax

```yaml
# Constants
constants:
  BUFFER_SIZE: {value: 1024, desc: "Buffer size"}
  ADDR_WIDTH: {eval: '($BUFFER_SIZE-1).bit_length()', desc: "Address width"}

# IP-local parameterizable constants/types
ipParameters:
  constants:
    IP_DATA_WIDTH: {value: 8, maxValue: 16, desc: "Per-instance data width"}
  types:
    ip_data_t: {width: IP_DATA_WIDTH, desc: "IP data word"}

# Types - width REQUIRED for non-enum types
types:
  byte_t: {width: 8, desc: "8-bit byte"}
  literal_param_t: {width: 8, maxBitwidth: 16, desc: "Literal-width parameterized type"}
  status_t:
    desc: "Status enum"  # width auto-calculated for enums
    enum:
      - {enumName: STATUS_IDLE, value: 0, desc: "Idle"}
      - {enumName: STATUS_BUSY, value: 1, desc: "Busy"}

# Structures
structures:
  packet_t:
    data: {varType: byte_t, desc: "Data field"}
    valid: {varType: bit_t, desc: "Valid flag"}

# Interfaces
interfaces:
  data_channel:
    interfaceType: rdy_vld
    desc: "Data channel"
    structures:
      - {structure: packet_t, structureType: data_t}

# Blocks
blocks:
  my_block:
    desc: "My block"
    hasRtl: true   # Default true
    hasMdl: true   # Default true
    params: [IP_DATA_WIDTH]  # Optional variant-bound parameters

# Instances
instances:
  u_my_block:
    container: top
    instanceType: my_block
    instGroup: main

# Connections (same container only)
connections:
  - {interface: data_channel, src: u_producer, dst: u_consumer}

# Variant parameter bindings
parameters:
  my_block:
    - {variant: variant0, param: IP_DATA_WIDTH, value: 8}
    - {variant: variant1, param: IP_DATA_WIDTH, value: 12}
```

If a block is RTL-enabled (`hasRtl: true`), every block instantiated inside it
must also be RTL-enabled. Model-only blocks (`hasRtl: false`) may only appear
under model-only parents; otherwise generated RTL will instantiate modules that
do not exist.

### Include Directives

Split architecture across files using `include:`:

```yaml
include:
  - shared/shared_types.yaml
  - dma/dma_block.yaml
```

Paths are relative to the including file. Include order matters -- define dependencies before dependents. Top-level file listing is in `project.yaml` under `projectFiles`.

### Connection Maps

Use `connectionMaps` to route interfaces across hierarchy boundaries:

```yaml
connectionMaps:
  - {interface: data_channel, block: subsystem, direction: src, instance: u_producer}
  - {interface: data_channel, block: subsystem, direction: dst, instance: u_consumer}
```

- `block`: The parent block whose boundary is being crossed
- `direction`: `src` if the internal instance is the source, `dst` if it is the destination
- `instance`: The internal instance to route to
- `port`: (Optional) Must match `srcport`/`dstport` if used in connection

### Eval Expressions in Constants

Constants support Python `eval` expressions referencing other constants with `$`:

```yaml
constants:
  DEPTH: {value: 256, desc: "Queue depth"}
  DEPTH_BITS: {eval: '($DEPTH-1).bit_length()', desc: "Bits for depth"}
  TOTAL_SIZE: {eval: '$DEPTH * 64', desc: "Total bytes"}
```

The `$CONSTANT_NAME` syntax references previously defined constants. Expressions are evaluated in definition order.

### Parameterizable Values

Use `ipParameters` in the IP-root YAML for constants/types that vary by instance or variant:

- Direct parameterizable constants require `maxValue > 0`.
- Direct literal-width parameterizable types require `maxBitwidth`.
- Derived constants/types inherit maximums from referenced parameterizable constants.
- Do not put `ipParameters` in shared include files that only define common constants/types/structures.
- If memory `wordLines` is an `ipParameters` constant or pure block param, address allocation uses the worst-case value.

## Common Pitfalls

### 1. Missing Width on Types
```yaml
# BAD - width required for non-enum types
types:
  data_t: {desc: "Data"}  # ERROR!

# GOOD
types:
  data_t: {width: 32, desc: "Data"}
```

### 2. Forgetting Manual Top-Level Decoder
You **MUST** manually create the top-level bus decoder:
```yaml
blocks:
  apb_decode_system:
    desc: "APB decoder"

instances:
  u_apb_decode_system:
    container: top
    instanceType: apb_decode_system
```
Block-level `<blockname>_regs` are auto-generated, but the top-level decoder is NOT.

### 3. Connections Across Containers
Connections only work within the **same container**. Use `connectionMaps` for hierarchy.

### 4. Model-Only Child Under RTL Parent
```yaml
# BAD - rtl_top.sv would instantiate model_only_child, but no RTL exists
blocks:
  rtl_top: {desc: "RTL top", hasRtl: true}
  model_only_child: {desc: "Behavioral model", hasRtl: false}

instances:
  u_top: {container: rtl_top, instanceType: rtl_top}
  u_child: {container: rtl_top, instanceType: model_only_child}

# GOOD - create RTL for the child, or make the parent model-only too
```

### 5. Missing addressGroup for Registers
Instances with registers need `addressGroup`:
```yaml
instances:
  u_my_block:
    container: top
    instanceType: my_block
    addressGroup: system  # Required for register access
```

### 6. Missing Worst-Case Bounds for Parameterizable Values
```yaml
# BAD - direct parameterizable constant without maxValue
ipParameters:
  constants:
    IP_DATA_WIDTH: {value: 8, desc: "Missing maxValue"}

# GOOD
ipParameters:
  constants:
    IP_DATA_WIDTH: {value: 8, maxValue: 16, desc: "Bounded width"}
```

## Interface Types Quick Reference

| Type | Protocol | Use Case |
|------|----------|----------|
| `rdy_vld` | Ready/Valid | Streaming data |
| `apb` | APB bus | Register access |
| `req_ack` | Request/Ack | Command/response |
| `push_ack` | Push with ack | FIFO writes |
| `pop_ack` | Pop with ack | FIFO reads |

## Reference
For complete YAML guidance: `builder/base/ARCH2CODE_AI_RULES.md`

For the definitive structure/data-type representation contract:
`builder/base/STRUCTURES_AND_DATA_TYPES_REFERENCE.md`
