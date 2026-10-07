---
name: design-types-structures
description: Guide for editing regular YAML constants, types and structures, which interfaces, registers and memories reference. For ipParameters and variant-bound types, use design-parameterizable-blocks.
---
# Skill: Design types and structures

## Purpose
Define regular constants, types and structures in arch2code YAML. Interfaces, registers and memories reference them. For `ipParameters`, parameterizable types and variant-bound structures, use `design-parameterizable-blocks.md`.

## References
*   `ARCH2CODE_AI_RULES.md`, section "Low-Level Architecture Elements".
*   `STRUCTURES_AND_DATA_TYPES_REFERENCE.md` covers what the YAML generates: SystemVerilog packed structs, SystemC storage, `_bitWidth`, `_byteWidth`, `_packedSt`, `sizeof(T)`, pack/unpack and thunkers.

## Definition order

A name must be visible where it is used. Inside one file, declare it in an earlier section than its use, so `constants:` comes before `types:`, and `types:` before `structures:`. For a name from another file, see `design-yaml-includes.md`.

## 1. Constants (`constants:`)

| Field | Meaning |
| :--- | :--- |
| `value` | Literal integer. Give `value` or `eval`, not both. |
| `eval` | SystemVerilog constant expression. Reference another constant as `$NAME`. |
| `desc` | Required. |
| `valueType` | `uint` (default), `int` or `real`. A `real` constant needs a literal `value`. |

```yaml
constants:
  DATA_WIDTH: {value: 64, desc: "Data bus width"}
  DEPTH:      {value: 256, desc: "Queue depth"}
  DEPTH_BITS: {eval: '$clog2($DEPTH)', desc: "Bits for a depth index"}
  TOTAL_SIZE: {eval: '$DEPTH * $DATA_WIDTH / 8', desc: "Total bytes"}
```

`eval` is a SystemVerilog integer constant expression:
*   It accepts integer literals in SV form (`255`, `8'hFF`, `'b1010`), `+ - * / %`, `& | ^ ~`, `<< >>`, comparisons, `?:`, `$clog2(...)`, `$NAME` and parentheses.
*   `/` is integer division and truncates toward zero.
*   `make db` rejects anything outside this list, including `**`, C-style `0x` literals and method calls such as `.bit_length()`.

Do not write `maxValue` on a regular constant. It makes the constant parameterizable. An `eval` that references a parameterizable constant derives its own `maxValue`, and `make db` rejects one written by hand. See `design-parameterizable-blocks.md`.

## 2. Types (`types:`)

| Field | Meaning |
| :--- | :--- |
| `width` | Bit width, an integer or a constant name. |
| `widthLog2` | Bits needed to hold the value N: 256 gives 9 bits. |
| `widthLog2minus1` | Bits needed to index N entries, 0 to N-1: 256 gives 8 bits. |
| `enum` | List of `{enumName, value, desc}`. `desc` is optional on an entry. |
| `isSigned` | Default `false`. |
| `desc` | Required. |

Give exactly one of `width`, `widthLog2` or `widthLog2minus1`. An enum type may omit all three. Its width is then the bit length of its largest value. A type with no width and no enum fails `make db`.

```yaml
types:
  byte_t:   {width: 8, desc: "8-bit byte"}
  addr_t:   {width: ADDR_WIDTH, desc: "Address"}
  index_t:  {widthLog2minus1: DEPTH, desc: "Index into DEPTH entries"}
  opcode_t:
    desc: "Operation code"
    enum:
      - {enumName: OP_READ,   value: 0, desc: "Read"}
      - {enumName: OP_WRITE,  value: 1, desc: "Write"}
      - {enumName: OP_CONFIG, value: 2, desc: "Config"}
```

`maxBitwidth` makes a type parameterizable, the same as `maxValue` on a constant. Leave it off regular types.

## 3. Structures (`structures:`)

Every key under a structure's name is a field. A structure has no `desc:` key. If you write one, `make db` warns `unknown field desc` and then stops with a Python error (`'str' object has no attribute 'get'`).

| Field property | Meaning |
| :--- | :--- |
| `varType` | A type name. |
| `subStruct` | A structure name, to nest it. Use `varType` or `subStruct`, not both. |
| `arraySize` | Element count, an integer or a constant. The default `0` means a scalar. Any value of 1 or more makes an array, so `1` gives a one-element array. |
| `desc` | Optional. |
| `generator` | Optional tag that adds generated accessors (see below). |

A field may give neither `varType` nor `subStruct` when a `variables:` entry of the same name is visible. The field then takes that variable's type and `desc`.

```yaml
variables:
  src_id: {type: byte_t, desc: "Source ID"}

structures:
  packet_header_t:
    dest_id: {varType: byte_t, desc: "Destination ID"}
    src_id: {}
    opcode: {varType: opcode_t, desc: "Operation code"}

  axi_data_t:
    data: {varType: datapath_t, desc: "Data payload"}
    strb: {varType: bit_t, arraySize: 4, desc: "Byte strobes"}

  full_packet_t:
    header:  {subStruct: packet_header_t, desc: "Packet header"}
    payload: {varType: byte_t, arraySize: 256, desc: "Payload data"}
```

### Field order

The first YAML field is the MSB of the packed value and the last field sits at bit 0. In `packet_header_t` above, `opcode` (a 2-bit enum) is bits `[1:0]` and `dest_id` is bits `[17:10]`. Every generated C++ struct declares the fields in reverse, last YAML field first. The firmware header also writes each field's packed range next to it:

```cpp
struct packet_header_t {
    opcode_t opcode; /* [1:0] */ //Operation code
    byte_t src_id; /* [9:2] */ //Source ID
    byte_t dest_id; /* [17:10] */ //Destination ID
    ...
};
```

Read bit positions from those comments, not from either declaration order. A range is an absolute bit index into the packed value, so in an 80-bit structure `[79:64]` is bits 15:0 of `_packedSt[1]`. An array field's range covers every element, with element 0 at the low end. A parameterizable structure gets no ranges, because its widths depend on the variant.

### Generator tags

*   `address` adds `_getAddress()` to the C++ struct. Address-bus payloads such as the APB address use it.
*   `data` adds `_getData()` and `_setData()`.
*   `tracker(name)` links the field to a debug tracker for transaction logging.

## Common pitfalls

1.  Using a name that is not visible. Declare it in an earlier section, or include the file that declares it (`design-yaml-includes.md`).
2.  Writing an `eval` outside the subset in section 1, such as `0x10` or `2**4`.
3.  Picking `widthLog2` for an index. It holds the value N itself, one bit more than indexing N entries needs when N is a power of two.
4.  Writing `arraySize: 1` for a scalar. Omit `arraySize`.
5.  Missing `desc` on a constant or type.
6.  Sizing a per-instance width with a regular constant. Declare it under `ipParameters:` and list it in the block's `params:` (`design-parameterizable-blocks.md`).

## Validation
Run `make db` to parse and validate the YAML.
