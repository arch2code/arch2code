# arch2code Structures and SystemC Pack / Unpack Design

**Audience:** arch2code maintainers, YAML authors defining `types` and
`structures`, RTL authors consuming generated SystemVerilog packages, and
SystemC model authors using or maintaining generated structures.

**Purpose:** Define the arch2code contract for structure and data type
representation across YAML, generated SystemVerilog, and generated SystemC.
This document is the definitive reference for why generated SystemC structures
use native C++ storage plus explicit pack/unpack conversion instead of storing
all fields directly as SystemC bit-precise data types.

When this document conflicts with the structure/type guidance in
`ARCH2CODE_AI_RULES.md`, this document is intended to supersede that guidance.
The AI rules should eventually be reduced to a short authoring summary that
points here for representation semantics.

---

## Source of truth: YAML types and structures

All architecture-visible data shapes are declared in YAML, not hand-written in
RTL or model code.

* `types` define hardware bit widths and, optionally, enum values.
* `structures` define ordered composites of `types` and nested structures.
* `arraySize` repeats a field in the packed hardware representation.
* Parameterizable constants and types carry both nominal dimensions and
  worst-case dimensions used for generated storage and address sizing.

The YAML declaration is the single source of truth. SystemVerilog and SystemC
are generated views of the same hardware data shape, but they do not use the
same host-language representation because the two languages serve different
jobs in the flow.

## SystemVerilog representation

In generated SystemVerilog packages, arch2code emits:

* constants as `localparam`;
* scalar types as `typedef logic[N-1:0]`;
* enums as typed SystemVerilog enums;
* structures as `typedef struct packed`.

A SystemVerilog packed struct is already a hardware-accurate representation:
each field occupies exactly its declared number of bits, with no C-style
padding. The first field declared in the packed struct occupies the most
significant end of the packed value, matching SystemVerilog packed-aggregate
semantics.

For example, this YAML:

```yaml
structures:
  ipDataSt:
    marker: {varType: enableT, desc: "Marker bit"}
    data:   {varType: ipDataT, desc: "Data word"}
```

generates a SystemVerilog packed struct with `marker` above `data` in the
packed value. If `marker` is 1 bit and `data` is 70 bits, then `marker` is bit
70 and `data` is bits 69:0. This is why older guidance says "the top field is
MSB."

## SystemC representation

Generated SystemC structures intentionally use native C++ storage for fields:

* small fields use the next native unsigned integer type large enough to hold
  the declared hardware width;
* very wide fields use generated word-array wrappers, typically backed by
  `uint64_t` words;
* generated metadata records the hardware dimensions separately:
  `_bitWidth`, `_byteWidth`, and `_packedSt`;
* `pack()` / `unpack()` convert between the C++ storage struct and the
  bit-accurate `_packedSt` representation;
* `sc_pack()` / `sc_unpack()` provide an `sc_bv<_bitWidth>` reference path used
  by generated tests and diagnostics.

The generated C++ struct member order is not the packed bit order. SystemC
codegen walks YAML fields in reverse when assigning packed bit positions, so
the least significant packed bits are filled first while the resulting packed
layout still matches the SystemVerilog packed struct. In the `ipDataSt` example
above, generated SystemC packs `data` at bit 0 and `marker` after it, yielding
the same bit layout as the SystemVerilog packed struct where YAML's first field
is the MSB.

This distinction is important:

* YAML field order defines the logical hardware layout.
* SystemVerilog directly represents that layout with a packed struct.
* SystemC stores convenient C++ fields and uses pack/unpack to produce the same
  hardware layout when data crosses a channel, thunker, register path, or
  model/RTL boundary.

## Why SystemC uses C++ storage instead of SystemC field types

### Modeling reality vs. C-type storage

arch2code generates SystemC models of hardware. In hardware, a *N*-bit field
is physically *N* bits — any value written above bit *N* simply does not
exist on those wires. RTL captures this exactly: the synthesis tools or
language semantics drop the overflow.

SystemC's native bit-precise types (`sc_int<N>`, `sc_uint<N>`,
`sc_bv<N>`, ...) reproduce the same behavior, but their runtime cost is
high enough that we avoid them in the generated model. Instead, the
generator promotes each HW-width field to the *next-larger native C type*
(or a `uint64_t[]` for fields above 64 bits). This gives the simulator
native arithmetic and makes debugging in a stock C++ debugger painless,
at the cost of carrying *more bits of storage than the field physically
has*.

That extra storage is the source of the design tension this document
addresses:

* **In RTL,** a 6-bit field cannot represent the value `0x80` — bit 7
  doesn't exist; the write silently drops the high bit.
* **In SystemC,** a 6-bit field is held in a `uint8_t` (or wider). A write
  of `0x80` *does* set bit 7 in that storage. Nothing physical drops it.

If the generated model silently masked that overflow out at every assignment
or every `pack()` call, the SystemC simulation would behave correctly but
the *algorithm* that wrote the over-large value would never be flagged.
That same algorithm would behave differently in RTL — where the bits would
have been physically dropped — and the model/RTL discrepancy would only
surface much later during tandem verification, integration, or silicon
bring-up.

The platform's position: **a SystemC overflow is, by definition, an
algorithm bug.** If RTL semantics would have dropped the bit, the SystemC
model must surface that overflow noisily so the author fixes the algorithm
rather than relying on the storage type to clean up after them.

Using `sc_uint<N>`, `sc_int<N>`, or `sc_bv<N>` for every generated field would
make field storage bit-precise, but it would also make generated models slower
and harder to debug. Native C++ storage keeps normal arithmetic fast and makes
values easy to inspect in a stock C++ debugger. The tradeoff is deliberate:
field storage may have more host bits than hardware bits, and the generated
pack/unpack boundary is responsible for enforcing and exposing the hardware
contract.

### No automatic zero-initialization

For the same reason, the generated structures **do not auto-zero** in their
default constructors. Hardware power-up state is undefined; relying on
zero-initialisation in the model would let bugs hide that would manifest
as undefined behaviour on the real device. Each writer is responsible for
fully populating the fields it produces.

The downside is that any path that *reads* a struct field before it is
fully written sees whatever was on the stack or in the heap. The
`pack()` / `unpack()` primitives below are aware of this — they each
control destination state explicitly rather than relying on the struct's
prior contents.

---

## Packed forms and bit-copy contracts

### The packed form

Every generated structure `S` has a sibling type `S::_packedSt`. The
packed form is a **bit-accurate** representation: every field occupies
exactly its declared bit width, packed back-to-back, with no padding.
This is the format that goes onto wires (the "channel payload" of every
generated `<proto>_channel<S>` instance), is compared against RTL in
tandem verification, and is the lingua franca between SystemC and RTL.

`_packedSt` is one of:

* `uintN_t` (scalar) for `_bitWidth <= 64`, where `N` is the smallest
  native C type that holds the bits.
* `uint64_t[K]` (array of 64-bit words) for `_bitWidth > 64`, with
  `K = ceil(_bitWidth / 64)`.

For non-parameterized structures, `_bitWidth`, `_byteWidth`, and `_packedSt`
are fixed by the single YAML definition.

For parameterized structures, the generated C++ type is templated on
`Config`. The active hardware width is computed from that `Config` (for
example, `Config::IP_DATA_WIDTH + 1`), but the C++ storage shape must be
compiled ahead of time. Any field or packed form whose width can vary by
variant is therefore represented using the **maximum** declared shape. A
templated structure whose active payload is 9 bits in one variant may still
have storage capable of holding the worst-case 71-bit variant. `_byteWidth`
identifies the active hardware byte footprint for the bound `Config`; the
underlying C++ storage may be larger because it was sized from the max
definition.

Conversion between the two representations (the C-storage struct form and
the bit-accurate packed form) is handled by:

* `void S::pack(S::_packedSt &_ret) const` — struct → packed.
* `void S::unpack(const S::_packedSt &_src)` — packed → struct.
* `sc_bv<S::_bitWidth> S::sc_pack() const` and
  `void S::sc_unpack(sc_bv<...>)` — the same conversion via the
  bit-precise `sc_bv` type, used by `test_ip_structs` as an
  independent reference implementation.

The thunkers (`<protocol>_port_thunker<UpT, DownT>` per
`builder/base/interfaces/<protocol>/`) bridge between two struct types
that share the same **active packed-form bit layout** using:

* `copy_packed_bits(OutPacked& out, const InPacked& in, uint16_t bits)`
  — packed → packed across struct types. The implementation lives in
  `common/systemc/bitTwiddling.h`.

Thunkers exist because "same bits" is not the same thing as "same C++ type."
Two structures can be layout-compatible at the hardware boundary while being
incompatible at the language boundary:

* a templated structure specialization and an untemplated structure are
  distinct C++ types even if their active field widths and packed payload bits
  are identical;
* two different generated struct names are distinct C++ types even if their
  YAML fields produce the same packed layout;
* a templated structure's storage is sized from the max definition, while an
  untemplated structure's storage is sized from its fixed definition.

The thunker therefore does not cast one struct to the other and does not assign
one channel payload type directly. It asks the upstream struct to produce its
active packed representation, copies exactly the downstream active bit count
into the downstream packed representation, and asks the downstream struct to
unpack those bits into its own C++ storage shape.

The Stage 6.2 compatibility check is the gate that makes this safe: it proves
that, for the bound variant, the source and destination structures describe the
same sequence of packed field widths. The C++ type system still sees
incompatible types; the thunker is the explicit representation conversion.

All three sit on top of two low-level primitives in
`common/systemc/bitTwiddling.{h,cpp}`:

* `pack_bits(...)` — three overloads, used by `pack()` codegen.
* `unpack_bits(...)` — one overload, used by `unpack()` codegen.

These helpers are internal generated-code support, not user-facing SystemC
model APIs. User code should not call `pack_bits()`, `unpack_bits()`, or
`copy_packed_bits()` directly. Use generated typed structures, channels,
ports, `pack()` / `unpack()` only at explicit representation boundaries, and
the generated register/memory APIs. If an agent or maintainer is modifying
`common/systemc/bitTwiddling.{h,cpp}`, they must read this document first; the
masking behavior is intentional and is part of the model/RTL equivalence
contract.

They have *deliberately different contracts*; the rest of this document
explains why.

---

## `pack_bits` — pack direction

### Contract (header)

```cpp
// pack_bits — append `bits` bits from src@srcPos to dest@destPos via
// bitwise OR. Caller must pre-clear the destination. Source words are NOT
// masked: any bits set above `consume` in a source word OR into the
// destination at the matching position. For the unpack direction, where
// source bits above `consume` must be discarded, use unpack_bits.
```

### Intent

`pack_bits` is the bit-copy primitive used by the generated `S::pack()`
to compose the packed form one field at a time. The composition pattern
is:

```cpp
void S::pack(_packedSt &_ret) const {
    memset(&_ret, 0, S::_byteWidth);   // pre-clear destination
    uint16_t _pos{0};
    pack_bits(&_ret, _pos, &fieldA, A_bits);   _pos += A_bits;
    pack_bits(&_ret, _pos, &fieldB, B_bits);   _pos += B_bits;
    pack_bits(&_ret, _pos, &fieldC, C_bits);   _pos += C_bits;
    ...
}
```

Each call OR-merges `field*_bits` bits from the struct member's storage
into `_ret` at the running offset `_pos`. The pre-clear `memset` ensures
the OR is equivalent to assignment for the bits each call writes.

`pack_bits` deliberately **does not mask** the source word to `bits` per
iteration. The expectation is that the struct member's storage holds *at
most* `bits` bits of meaningful value. If it holds more — i.e. the struct
field has been written with a value larger than its declared HW width —
those extra bits flow through into `_ret` at the position the *next*
field will occupy. They appear as corruption of an adjacent packed-form
field.

This is the canonical fail-fast surface: the corruption is then caught by
**`test_ip_structs`**, an auto-generated roundtrip canary that compares
the result of `S::pack` / `S::unpack` against the equivalent `S::sc_pack`
/ `S::sc_unpack` reference (which *does* mask, via `sc_bv` range
semantics). The mismatch fires the canary and points at the algorithm
bug rather than letting it slip through.

Adding source masking to `pack_bits` would silently sanitize the overflow
and remove that surface. **Do not change `pack_bits` to mask without
first relocating the detection mechanism elsewhere** (for example, a
per-field bounds assert at the call site of the offending writer).

### Caller responsibilities

* Pre-clear the destination. `pack()` does this with a single
  `memset(&_ret, 0, _byteWidth)` at the top. Without the pre-clear, the
  OR pattern accumulates stale bits.
* Provide source storage that holds at most `bits` bits of meaningful
  value. If the writer overflows, accept that the surface is the
  `test_ip_structs` canary.

### Where it's emitted

`templates/systemc/structures.py` emits `pack_bits` calls from the
`pack()` codegen:

* Line 1261 — by-value form for fields with a single ≤64-bit storage
  word.
* Line 1264 — by-pointer form for parameterizable / wide fields.
* Line 1329 — by-value form for nested-struct staging.

The non-templated paths (when no field is `Config`-dependent) reach the
same primitives.

---

## `unpack_bits` — unpack direction

### Contract (header)

```cpp
// unpack_bits — extract `bits` bits from src@srcPos to dest@destPos via
// bitwise OR. Caller must pre-clear the destination. Each iteration's
// source word is masked to exactly `consume` bits before OR-ing, so bits
// above `consume` (adjacent fields in a packed form) are dropped. For the
// pack direction, where bits above `consume` must propagate, use pack_bits.
```

### Intent

`unpack_bits` is the bit-extraction primitive used by the generated
`S::unpack()` to pull one field at a time out of a packed form into the
struct's C-typed storage:

```cpp
void S::unpack(const _packedSt &_src) {
    uint16_t _pos{0};
    memset(&fieldA, 0, sizeof(fieldA));
    unpack_bits(&fieldA, 0, &_src, _pos, A_bits);   _pos += A_bits;
    memset(&fieldB, 0, sizeof(fieldB));
    unpack_bits(&fieldB, 0, &_src, _pos, B_bits);   _pos += B_bits;
    ...
}
```

Each call extracts `bits` bits from `_src` at the running offset `_pos`
and writes them into the struct member's storage at offset 0. The per-
field `memset` provides the clean destination required by the OR pattern.

`unpack_bits` **does mask** each iteration's source word to exactly the
`consume` count for that iteration. Here the source — the packed form —
legitimately carries adjacent fields' bits above the field being
extracted. For example, in `ipDataSt<Config>` with `IP_DATA_WIDTH=70`:

* bits 0..69 of the packed form are `data`,
* bit 70 is `marker`.

When `unpack_bits` is invoked to extract the 70-bit data field, its
second iteration consumes only the low 6 bits of packed word[1]. The
marker bit at packed-position 70 sits at bit 6 of that same word and
must *not* propagate into `data.word[1]`. The per-iteration source mask
is what drops it.

This is the direct inverse of `pack_bits`'s contract: where pack-side
overflow must be visible, unpack-side adjacent-field bits must be
invisible. If `unpack_bits` did *not* mask, the marker bit would leak
into the data field's "storage > declared width" region, and the
subsequent algorithm-side check (e.g. `Q_ASSERT(data.data.word[1] ==
0x2A)`) would fire for the wrong reason — the data is correct on the
wire, but the unpack path corrupted it.

### Caller responsibilities

* Pre-clear the destination field. The templated `unpack()` codegen
  emits `memset(&field, 0, sizeof(field))` immediately before each call.
* Provide a source that is a valid packed form (i.e. produced by some
  `S::pack` or `copy_packed_bits` upstream). The mask handles legitimate
  adjacent-field bits; it does **not** validate that the destination's
  "storage > declared width" region was zero on entry. That validation,
  if desired, is out-of-band — see "Where overflow lives" below.

### Where it's emitted

`templates/systemc/structures.py` emits `unpack_bits` calls from the
`unpack()` codegen for the cases that previously used `pack_bits`:

* Line 1085 — array-backed parameterizable field unpack. The codegen
  also emits the matching `memset(&field, 0, sizeof(field))`.
* Line 1170 — misaligned nested-struct staging copy into a value-
  initialised `_packedSt _tmp{0}`, where the destination clear is
  already provided by the value-init.

The non-templated scalar unpacks (lines 1124–1144) do their masking
inline with explicit `((src >> pos) & ((1ULL << bits) - 1))` rather than
calling either primitive; the contract is the same.

---

## `copy_packed_bits` — thunker bridge

### Contract

```cpp
template <typename OutPacked, typename InPacked>
inline void copy_packed_bits(OutPacked& out, const InPacked& in, uint16_t bits);
```

Copies `bits` bits of bit-accurate payload from `in` to `out`, where the
two operand types are the `_packedSt` of two different struct types that
share the same active packed-form layout for the bound variant (verified at
YAML-processing time by the Stage 6.2 packed-form compatibility check).

`copy_packed_bits` **always clears its destination first** (the
implementation zeros every word of `out` before copying). This is the
half of the thunker's "appropriate destination" contract that the helper
takes responsibility for; the caller does not need to pre-clear `out`.

### Intent

The thunker's forwarding loop is:

```cpp
while (true) {
    UpT   inVal;            // stack, uninitialised — modelling HW
    DownT outVal;           // stack, uninitialised
    typename UpT::_packedSt inPacked;
    typename DownT::_packedSt outPacked;

    up->pushReceive(inVal);              // populate inVal
    inVal.pack(inPacked);                // pack() pre-clears inPacked
    copy_packed_bits(outPacked, inPacked, DownT::_bitWidth);
                                         // copy_packed_bits pre-clears outPacked
    outVal.unpack(outPacked);            // unpack() pre-clears each field
    m_chDown.push(outVal, (uint64_t)-1);
    up->ack();
}
```

`UpT::_packedSt` and `DownT::_packedSt` may not be the same C++ type. In the
common parameterized-to-fixed case, the upstream templated structure's
`_packedSt` is selected from its maximum possible width, while the downstream
fixed structure's `_packedSt` is selected from its one concrete width. The
active payload can still be identical for the chosen variant. The thunker
bridges that case by copying only `DownT::_bitWidth` active bits from one
packed storage shape to the other.

Each stage owns the cleanliness of its own output:

* `pack()` clears `inPacked` (its `memset(&_ret, ...)`).
* `copy_packed_bits` clears `outPacked` before the bit copy.
* `unpack()` clears each destination field before its `unpack_bits` call.

No stage relies on the local struct variable being zero on entry — that
preserves the "model does not auto-zero" stance — and no stage relies on
any *prior* stage to clean up after it.

---

## Where overflow lives

A "true overflow" — a writer storing a value above the declared HW bit
width into a struct field — propagates from the writer through the
SystemC simulation as follows:

1. **Writer assigns the field.** The over-large value is stored in the
   native C-type backing the field. No SystemC code is involved.

2. **Producer calls `pack()`.** `pack_bits` reads the storage without
   masking. Overflow bits flow into `_ret` at the positions of *adjacent*
   packed-form fields, corrupting them.

3. **Wire transport / thunker / channel.** Bit-accurate. No reshape.

4. **Consumer calls `unpack()`.** `unpack_bits` correctly extracts each
   field with masking, but the bits being extracted are *not what the
   writer intended* because of the upstream corruption in step 2.

5. **Algorithm-side check fires.** The downstream consumer's assertion
   on the corrupted adjacent field, *or* the `test_ip_structs` roundtrip
   canary, *or* a model/RTL tandem mismatch surfaces the bug.

The canonical artefact that catches this in CI is **`test_ip_structs`**.
It is auto-generated for every parameterizable structure and runs at
testbench startup; it produces patterned packed inputs, runs them
through both `unpack`/`pack` and `sc_unpack`/`sc_pack` (the bit-precise
reference), and asserts the two paths agree. Any divergence — including
overflow corruption — fires `Q_ASSERT(false, "<struct> fail")` with the
patterned diagnostics dumped to the log.

The deliberate non-masking of `pack_bits` is what makes that canary
fire. Removing it would silence the canary for any algorithm bug that
happens to clip cleanly to the field's declared width.

---

## Quick reference — when to use what

| Direction | Caller | Helper | Source masked? | Caller clears dest? |
|---|---|---|---|---|
| `pack()` field write | `S::pack(_ret)` | `pack_bits` | No — surface overflow | Yes (`memset(&_ret, 0, _byteWidth)` once at top of `pack()`) |
| `unpack()` field read (array-backed) | `S::unpack(_src)` | `unpack_bits` | Yes — drop adjacent fields | Yes (per-field `memset(&field, 0, sizeof(field))` before each call) |
| `unpack()` field read (scalar) | `S::unpack(_src)` | inline `(src >> pos) & ((1ULL << bits) - 1)` | Yes — explicit mask | N/A (direct assignment) |
| Thunker packed→packed bridge | `<proto>_port_thunker::thunk` | `copy_packed_bits` | N/A | No (helper clears `out`) |

## Quick reference — what to never do

* Do not add source masking to `pack_bits`. You will hide every algorithm
  bug that overflows a declared HW width.
* Do not add automatic zero-initialisation to generated struct default
  constructors. The model deliberately mirrors HW power-up state.
* Do not bypass `unpack_bits` and call `pack_bits` from a generated
  `unpack()`. You will get the same adjacent-field leakage the Stage 8.2
  fixture surfaced.
* Do not "fix" a `test_ip_structs` failure by editing the canary. The
  canary is doing exactly what it was built for.

---

## YAML authoring rules this document owns

`ARCH2CODE_AI_RULES.md` may keep a short checklist, but the following
representation rules belong here:

* Define architecture-visible data widths in YAML `types`, not in handwritten
  SystemVerilog or SystemC.
* Use enums for named state, opcode, mode, and command values. Enum width is
  derived from the largest enum value unless a width is explicitly supplied.
* Define interface, register, and memory payloads as YAML `structures`.
* Use `varType` for scalar typed fields and `subStruct` for nested structures;
  do not use both on the same field.
* Treat YAML field order as hardware-significant. The first field is the MSB
  side of the packed SystemVerilog value; generated SystemC reverses traversal
  internally so its `_packedSt` has the same bit layout.
* Use `arraySize` only for fixed architectural repetition. Each element
  contributes its declared bit width to the packed representation.
* Do not hand-write generated structure metadata such as `isParameterizable`,
  `maxBitwidth`, `_bitWidth`, `_byteWidth`, or `_packedSt`.
* For parameterizable structures, define the parameterizable constants and
  types under `ipParameters`; arch2code derives structure parameterization and
  worst-case widths from the referenced fields and array sizes.
* Never infer hardware byte footprint from C++ `sizeof(struct)`. Use
  `_bitWidth` / `_byteWidth` for hardware dimensions and `pack()` / `unpack()`
  for representation conversion.

---

## Pointers

* **Runtime primitives:** `common/systemc/bitTwiddling.{h,cpp}`
* **Codegen that emits the primitives:** `templates/systemc/structures.py`
  (search for `pack_bits` / `unpack_bits`)
* **Per-protocol thunker headers:** `builder/base/interfaces/<protocol>/<protocol>_port_thunker.h`
* **`copy_packed_bits` template:** `common/systemc/bitTwiddling.h`
* **Canary template:** `templates/systemc/structures.py`, search for
  `testStructsCPP`
* **Compatibility check that gates cross-interface thunker emission:**
  `pysrc/processYaml.py::validatePorts` (Stage 6.2 of
  `plan-variant-config-unification.md`)
* **Why the design exists:** this document.
