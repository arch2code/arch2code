---
name: design-types-structures
description: Guide for editing YAML types, structures, and constants - the foundational elements that interfaces, registers, and memories reference
---
# Skill: Design Types & Structures

## Purpose
Guide the user in defining constants, types, and structures in arch2code YAML. These are the foundational elements referenced by interfaces, registers, and memories.

## References
*   **Main Rules:** `ARCH2CODE_AI_RULES.md` (See "Low-Level Architecture Elements")

## Definition Order

Define in dependency order -- later elements reference earlier ones:
1. **Constants** -- parameters and sizing
2. **Types** -- bit widths and enums
3. **Structures** -- composite data (reference types)

## Instructions

### 1. Constants (`constants` dictionary)

Fixed parameters used for sizing, addresses, and configuration.

**Properties:**
*   `value`: Literal integer. **Use `value` OR `eval`, not both.**
*   `eval`: Python expression string. Reference other constants with `$NAME`.
*   `maxValue`: Optional worst-case integer for parameterizable constants.
*   `isParameterizable`: Optional explicit flag; normally use `ipParameters` instead.
*   `desc`: **(Required)** Description.

```yaml
constants:
  DATA_WIDTH: {value: 64, desc: "Data bus width"}
  DEPTH: {value: 256, desc: "Queue depth"}
  DEPTH_BITS: {eval: '($DEPTH-1).bit_length()', desc: "Bits for depth index"}
  TOTAL_SIZE: {eval: '$DEPTH * $DATA_WIDTH // 8', desc: "Total bytes"}
  IP_DATA_WIDTH: {value: 8, maxValue: 16, desc: "Per-instance data width"}
```

**Eval rules:**
*   `$CONSTANT_NAME` references previously defined constants
*   Expressions are Python and evaluated in definition order
*   Standard Python operators and builtins are available (e.g., `bit_length()`, `//`, `**`)
*   If an `eval` references a parameterizable constant, `maxValue` is auto-derived; do not hand-write it

### 2. Types (`types` dictionary)

Define bit-vector widths and enumerations.

**Properties:**
*   `width`: **(Required for non-enum types)** Bit width (integer or constant name).
*   `widthLog2` / `widthLog2minus1`: Alternatives for address/index widths.
*   `maxBitwidth`: Optional worst-case bit width for parameterizable types.
*   `isParameterizable`: Optional explicit flag; normally use `ipParameters` instead.
*   `desc`: **(Required)** Description.
*   `enum`: (Optional) List of enum values. Width is auto-calculated from max value.

```yaml
types:
  # Simple bit-vector types
  byte_t: {width: 8, desc: "8-bit byte"}
  addr_t: {width: ADDR_WIDTH, desc: "Address type (width from constant)"}
  ip_data_t: {width: IP_DATA_WIDTH, desc: "Width derives maxBitwidth from parameter"}
  ip_literal_t: {width: 8, maxBitwidth: 16, desc: "Literal width with worst-case max"}
  
  # Enum types (width auto-calculated)
  opcode_t:
    desc: "Operation code"
    enum:
      - {enumName: OP_READ, value: 0, desc: "Read operation"}
      - {enumName: OP_WRITE, value: 1, desc: "Write operation"}
      - {enumName: OP_CONFIG, value: 2, desc: "Config operation"}
```

**Common pitfall -- missing width:**
```yaml
# BAD - width required for non-enum types
types:
  data_t: {desc: "Data"}  # ERROR!

# GOOD
types:
  data_t: {width: 32, desc: "Data"}
```

### 3. Parameterizable IP Parameters (`ipParameters` dictionary)

Use `ipParameters` in an IP block's own YAML file for constants and types that vary by instance or variant. Entries are processed through the normal `constants` and `types` schemas, then marked parameterizable.

```yaml
ipParameters:
  constants:
    IP_DATA_WIDTH: {value: 8, maxValue: 16, desc: "Per-instance data width"}
    IP_MEM_DEPTH: {value: 16, maxValue: 32, desc: "Per-instance memory depth"}
    IP_DATA_WIDTH_X2: {eval: "$IP_DATA_WIDTH * 2", desc: "Derived max auto-computed"}
  types:
    ip_data_t: {width: IP_DATA_WIDTH, desc: "Data type"}
```

**Rules:**
*   Direct parameterizable constants require `maxValue > 0`.
*   Direct parameterizable types require `maxBitwidth`, unless their width references a parameterizable constant.
*   Derived constants/types inherit parameterizability from referenced constants.
*   Do not place `ipParameters` in shared include files that only define common constants/types/structures.

### 4. Structures (`structures` dictionary)

Composite data types built from types or other structures.

**Field properties:**
*   `varType`: **(Required unless using `subStruct`)** Type name from `types`.
*   `subStruct`: (Alternative to `varType`) Nest another structure.
*   `desc`: **(Required)** Description.
*   `arraySize`: (Optional) Fixed array size. **Default: `1`**
*   `generator`: (Optional) Code generation tag (e.g., `address`, `data`, `tracker(name)`).
*   `local`: (Optional) Field exists only in model, not in RTL. **Default: `false`**

```yaml
structures:
  # Simple structure
  apb_addr_t:
    address: {varType: dword32_t, generator: address, desc: "APB address"}
  
  # Structure with multiple fields
  packet_header_t:
    dest_id: {varType: byte_t, desc: "Destination ID"}
    src_id: {varType: byte_t, desc: "Source ID"}
    opcode: {varType: opcode_t, desc: "Operation code"}
  
  # Structure with array field
  axi_data_t:
    data: {varType: datapath_t, desc: "Data payload"}
    strb: {varType: bit_t, arraySize: 4, desc: "Byte strobes"}
    last: {varType: bit_t, desc: "Last transfer flag"}
  
  # Nested structure
  full_packet_t:
    header: {subStruct: packet_header_t, desc: "Packet header"}
    payload: {varType: byte_t, arraySize: 256, desc: "Payload data"}
  ip_burst_t:
    samples: {varType: ip_data_t, arraySize: IP_MEM_DEPTH, desc: "Parameterized burst"}
  
  # Structure with tracker for debug
  command_t:
    cmd: {varType: opcode_t, generator: tracker(cmd), desc: "Tracked command"}
    addr: {varType: dword32_t, desc: "Target address"}
```

**Generator tags:**
*   `address` -- marks the field as an address (used by register bus generation)
*   `data` -- marks the field as data (used by register bus generation)
*   `tracker(name)` -- links to a debug tracker for transaction tracing

## How YAML Width Maps to Generated C++

The YAML `width` on a type becomes the type's hardware bit width in generated code. Each generated C++ structure carries:

*   `_bitWidth` — **HW bit width**, the sum of all field widths from YAML. Used for `sc_bv<>` sizing, pack/unpack, and address-map calculations.
*   `_byteWidth` — **HW byte width**, `(_bitWidth + 7) >> 3`. Used for register/memory byte footprint.
*   `_packedSt` — C++ type for the bit-packed HW representation (selected to fit `_bitWidth`).

These are **not** the same as C++ `sizeof(struct)`. C++ storage types are typically wider than the HW fields they model (e.g., a 1-bit YAML type becomes `uint8_t` in C++). A structure with three 1-bit fields has `_byteWidth = 1` but `sizeof = 3`. The `pack()` / `unpack()` methods bridge between C++ layout and HW-accurate bit packing.

For parameterizable structures, arch2code also computes worst-case metadata (`isParameterizable`, `maxBitwidth`) from parameterizable field types, sub-structures, and `arraySize` constants. Users should not write those structure metadata fields directly.

## Common Pitfalls

1.  **Referencing undefined types:** Types must be defined before use. If in a separate file, use `include:` to pull in dependencies.
2.  **Using `varType` and `subStruct` together:** Choose one per field, not both.
3.  **Forgetting `desc`:** Required on every element (constants, types, structures, fields).
4.  **Missing `width` on non-enum types:** Only enums auto-calculate width.
5.  **Missing `maxValue` / `maxBitwidth`:** Direct parameterizable constants/types need explicit worst-case bounds unless the bound can be derived from another parameterizable constant.

## Validation
*   Run `make db` to parse and validate all YAML definitions.
