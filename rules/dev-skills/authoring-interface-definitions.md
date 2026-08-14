---
name: authoring-interface-definitions
description: How to author an Arch2Code `interface_defs` entry - entry layout, the hand-written companion files it names, and the declaration rules the contract test enforces. Use when adding or changing an interface protocol.
---

# Authoring an Interface Definition

An interface protocol is declared by an `interface_defs:` entry. The shipped definitions live one per directory under `interfaces/`, next to the hand-written files that implement the protocol, and are loaded into every project through the `systemFiles:` list in `config/project.yaml`. A project may also declare `interface_defs:` in any of its own `projectFiles:`; a project-local definition is read exactly the same way.

## Entry Layout

An `interface_defs:` entry is keyed by the interface type name and carries the following sections.

- `parameters:` - the payload structures the interface carries, in declaration order. Each entry declares `datatype: struct`, and adds `optional: true` for a payload a declaring interface may leave unbound. An `interfaces:` entry binds them by name, through the `structureType:` field of its `structures:` list. The section is omitted for a protocol with no payload.
- `hdlparams:` - widths derived from a bound payload rather than declared directly. Each entry declares `datatype: integer`, `isEval: true`, and a `value:` of the form `<parameter>.<expression>`, where the parameter is a `parameters:` entry and `to_bytes()` is the expression the evaluator provides.
- `signals:` - the wires of the protocol, mapping each signal name to its type. A type may name a `parameters:` entry, an `hdlparams:` entry, `bool`, or a literal HDL type such as `bit [3:0]`, which is emitted verbatim. Declaration order is the order the flattened boundary ports are emitted in.
- `modports:` - one entry per modport, `src` and `dst`, each listing every signal under `inputs:` or `outputs:` from that modport's point of view.
- `sc_channel:` - `type:` is the prefix of the hand-written SystemC class names described below. `multicycle_types:` lists the transactional modes the channel supports. `param_cast:`, `thunker:` and `set_initial_value:` are optional.
- `multiDst:` - allows a connection of this type to have more than two ends.
- `addressBus:` - marks the definition as a register or address bus meta-protocol.
- `mappedFrom:` - lists the register and memory type aliases, such as `reg_ro` and `reg_rw`, that resolve to this definition.

## Companion Files

The definition names the protocol, it does not generate the implementation. For a definition whose `sc_channel.type:` is `myproto`, the generator emits references to hand-written files that must exist:

- `myproto_if.sv` - the SystemVerilog interface and its `src` and `dst` modports.
- `myproto_channel.h` - the SystemC channel `myproto_channel` and the ports `myproto_in` and `myproto_out`.
- `myproto_bfm.h` - `myproto_src_bfm`, `myproto_dst_bfm`, and the Verilated bridge `myproto_hdl_if` used by the generated HDL wrappers.
- `myproto_port_thunker.h` - `myproto_port_thunker`, needed only where the protocol is used in a cross-interface bind.

Every one of these names is built from `sc_channel.type:` rather than from the interface type name. Every shipped definition sets the two equal, which is convention and not a requirement: a definition that points `sc_channel.type:` at another protocol generates consistent code against that protocol's classes.

## Declaration Rules

`unittest/test_interface_def_contracts.py` checks the rules below over every definition in the shipped interface trees. They are data contracts between the definition and the generator, and they are not expressible in the schema, so nothing else checks them. Most violations produce wrong generated code rather than a generation failure, so run the suite after editing a definition:

```bash
cd unittest && python3 test_interface_def_contracts.py
```

1. **Optional struct parameters are declared last.** Every parameter marked `optional: true` must come after every parameter that is not. Struct parameters become positional C++ template arguments, and the hand-written BFM and thunker templates splice another argument group into the middle of that list. The generator builds those signatures by splitting the declared parameter list at its first optional parameter. That split only produces the right argument order, and only stays a split rather than becoming a reorder, when the optional parameters form the tail of the list.
2. **An `isEval` hdlparam evaluates a required struct parameter.** The width an `isEval` hdlparam supplies is always needed, because the generator has no way to omit the signal it types. An optional parameter may be left unbound, and an unbound parameter carries no structure and so no width.
3. **Every modport lists every declared signal.** A signal must appear under `inputs:` or `outputs:` of every modport. The generator gives a flattened boundary port its direction by asking whether the signal is in that modport's `inputs:` group and calling it an output otherwise, so a signal no group mentions takes its direction from that fallback instead of from the definition.
4. **An `isEval` hdlparam `value:` has exactly one `.` separator.** The generator splits the value on `.` into exactly the parameter to read and the expression to evaluate against it.
5. **Every parameter declares `datatype: struct`.** This is the only parameter datatype the generator recognises. A parameter declaring anything else is skipped when the payload bindings are built, so it disappears from the positional C++ template arguments and from the SystemVerilog parameter binding, and every argument declared after it shifts one place.

The suite walks the shipped interface trees only. A definition a project declares in its own YAML is subject to the same rules, because the generator makes no distinction between the two, but nothing validates it automatically. Checking a project-local definition against this list is the author's responsibility.

## Related

- The transactional modes named by `multicycle_types:` are described in the `Trackers & Interfaces` documentation page.
- The interfaces themselves are described in the `Description of Common Interfaces` documentation page.
