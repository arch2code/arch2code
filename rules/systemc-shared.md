---
description: SystemC conventions shared across model/ and tb/ directories
globs: "model/**/*.cppm, model/**/*.cpp, model/**/*.h, tb/**/*.cppm, tb/**/*.cpp, tb/**/*.h"
alwaysApply: false
---
# SystemC shared rules

These rules apply to both `model/` and `tb/`.

Never edit `base/<block>Base.cppm`, the generated `model/<includeName>Includes.cppm` files, or code between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END`. `systemc-core` section 2 lists the user slots.

## Structure sizing

Generated structures carry hardware widths and a packed form that differ from C++ object storage.

- Never assume `sizeof(T)` equals `T::_byteWidth`.
- Do not call the bit-packing helpers (`pack_bits`, `unpack_bits`, `copy_packed_bits`) from model or testbench code.
- Use the typed generated structures, channels, ports, and register and memory APIs.

`builder/base/STRUCTURES_AND_DATA_TYPES_REFERENCE.md` defines the packed representation.

## Where the rest lives

*   Logging, registers, memories and threads: `systemc-core`.
*   Port calls: `systemc-interfaces`.
*   Full API: `builder/base/SYSTEMC_API_USER_REFERENCE.md`.
