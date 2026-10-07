---
name: authoring-interface-definitions
description: How to author an Arch2Code `interface_defs` entry - entry layout, the hand-written companion files it names, and the declaration rules the schema and the contract test enforce. Use when adding or changing an interface protocol.
---

# Authoring an interface definition

An `interface_defs:` entry declares an interface protocol. Base ships one definition per directory under `builder/base/interfaces/`, next to the hand-written files that implement it. Pro ships its own under `builder/pro/interfaces/`. A project loads them through the `systemFiles:` list in `builder/base/config/project.yaml` and `builder/pro/config/project.yaml`, so a new shipped definition needs a line there. A project may also declare `interface_defs:` in its own `projectFiles:`, and the generator reads it the same way.

`builder/base/interfaces/rdy_vld/rdy_vld_if.yaml` is the smallest complete example. The schema is the `interface_defs:` section of `builder/base/config/schema.yaml`.

## Entry layout

The entry key is the interface type name. The sections are:

- `parameters:` lists the payloads the interface carries, in declaration order. An `interfaces:` entry binds each one by name through `structureType:` in its `structures:` list. Each parameter declares a `datatype:`:
  - `struct` binds a `structures` row and is one C++ template argument.
  - `type` binds a `types` row and is two template arguments, the name and the width. `axi_read` declares `id_t` this way.
  - `typeStruct` binds either kind and is also two arguments.

  `optional: true` lets a declaring interface leave the payload unbound. `defaultWidth:` (default 1) is the width of the signals an unbound optional parameter types. A protocol with no payload writes `parameters: {}` or omits the section.
- `hdlparams:` lists widths derived from a bound payload. Each entry declares `datatype: integer`, `isEval: true`, and a `value:` of the form `<parameter>.<expression>`, such as `data_t.to_bytes()`.
- `signals:` maps each wire to its type: a `parameters:` entry, an `hdlparams:` entry, `bool`, or a literal HDL type such as `bit [3:0]`, emitted verbatim. Flattened boundary ports follow this order.
- `modports:` has `src` and `dst`. Each lists every signal under `inputs:` or `outputs:`, from that end's point of view.
- `sc_channel:` names the SystemC side.
  - `type:` is the prefix of the channel, port, BFM and thunker class names.
  - `multicycle_types:` lists the transactional modes the channel supports.
  - `set_initial_value: true` makes a channel created for a register connection start at the register's default value. `status` and `external_reg` set it.
  - `param_cast:` wraps the channel's template arguments in the named template. No shipped definition uses it.
  - The generator never reads `thunker:`. Leave it out.
- `socket:` is keyed by modport. Each entry sets `kind: drive` or `kind: observe`. `observe: true` adds an `_obs` observe connection, and `lockstep: true` adds the `pysocket_sync` connection. Leave out an end that has no socket shell.
- `multiDst: true` allows a connection of this type to have more than two ends.
- `addressBus: true` marks a register or address bus meta-protocol.
- `mappedFrom:` lists the register and memory type aliases, such as `reg_ro` and `reg_rw`, that resolve to this definition.

## Companion files

The definition names the protocol. It does not generate the implementation. The generator emits `#include` lines and class names for hand-written files, and some names come from the interface key while others come from `sc_channel.type`. For key `myproto` with `sc_channel.type: myproto`:

| File | Name built from | Contents |
| :--- | :--- | :--- |
| `myproto_if.sv` | interface key | SV interface `myproto_if` with `src` and `dst` modports |
| `myproto_channel.h` | `sc_channel.type` | `myproto_channel`, `myproto_in`, `myproto_out` |
| `myproto_bfm.h` | interface key | `myproto_src_bfm`, `myproto_dst_bfm` and the Verilated bridge `myproto_hdl_if`, whose class names come from `sc_channel.type` |
| `myproto_port_thunker.h` | `sc_channel.type` | `myproto_port_thunker`, used where the protocol takes part in a cross-interface bind |
| `myproto_port_socket.h` | interface key | socket shell, needed only when the definition has `socket:` |
| `myproto_port_tee.h` | interface key | Pro tandem tee, in `builder/pro/common/systemc/` |

Every shipped definition sets `sc_channel.type` equal to its key. Keep them equal. A definition that points `sc_channel.type` at another protocol mixes two sets of names.

## Declaration rules

The schema enforces rule 5, so a misdeclared parameter stops `make db`. `builder/base/unittest/test_interface_def_contracts.py` checks the other rules over every definition under `builder/base/interfaces/` and `builder/pro/interfaces/`. Run it after you edit a shipped definition:

```bash
python3 builder/base/unittest/test_interface_def_contracts.py
```

1. **Optional parameters come last.** Declare every `optional: true` parameter after every required one. The generator builds the BFM and thunker signatures by splitting the parameter list at its first optional parameter and splicing another argument group between the halves. A required parameter after an optional one lands in the wrong argument slot, and generation still succeeds.
2. **An `isEval` hdlparam evaluates a required `struct` parameter.** The signal it types is always declared, so its width must always exist. An unbound optional parameter has no width, and generation fails for an interface that leaves it unbound.
3. **Every modport lists every signal.** The generator makes a signal an input when it is in the modport's `inputs:` and an output otherwise. A signal missing from a modport becomes an output, the wrapper drives it backwards, and generation still succeeds.
4. **An `isEval` `value:` has exactly one `.`.** The generator splits the value on `.` into the parameter and the expression. Any other count aborts generation with a bare `ValueError`.
5. **Every parameter declares `datatype:` as `struct`, `type` or `typeStruct`.** Any other value fails the schema check.
6. **Only an optional parameter sets `defaultWidth:` other than 1.** A required parameter is always bound, so the generator never reads its `defaultWidth`, and the value misleads the reader.

The schema check covers a project-local definition, so rule 5 applies to it. The test walks only the shipped trees, so check a project-local definition against rules 1 to 4 and 6 by hand.
