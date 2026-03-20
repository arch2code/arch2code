# Architecture YAML Rules

## Overview
YAML files in `arch/yaml/` define the hardware architecture. YAML is the **Single Source of Truth** - all implementation artifacts are generated from these definitions.

## Key Patterns

### Definition Order
Define elements in dependency order:
1. **Constants** - Parameters and sizing
2. **Types** - Bit widths and enums
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

# Types - width REQUIRED for non-enum types
types:
  byte_t: {width: 8, desc: "8-bit byte"}
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

# Instances
instances:
  u_my_block:
    container: top
    instanceType: my_block
    instGroup: main

# Connections (same container only)
connections:
  - {interface: data_channel, src: u_producer, dst: u_consumer}
```

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

### 4. Missing addressGroup for Registers
Instances with registers need `addressGroup`:
```yaml
instances:
  u_my_block:
    container: top
    instanceType: my_block
    addressGroup: system  # Required for register access
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
For complete documentation: `builder/base/ARCH2CODE_AI_RULES.md`
