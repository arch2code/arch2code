---
name: authoring-interface-definitions
description: How to author an Arch2Code `interface_defs` entry - entry layout, the hand-written companion files it names, and the declaration rules the schema and the contract test enforce. Use when adding or changing an interface protocol.
---

# Authoring an interface definition

An `interface_defs:` entry declares an interface protocol. Base ships one definition per directory under `builder/base/interfaces/`, next to the hand-written files that implement it. Pro ships its own under `builder/pro/interfaces/`. A project loads them through the `systemFiles:` list in `builder/base/config/project.yaml` and `builder/pro/config/project.yaml`, so a new shipped definition needs a line there. A project may also declare `interface_defs:` in its own `projectFiles:`, and the generator reads it the same way.

`builder/base/interfaces/rdy_vld/rdy_vld_if.yaml` is the smallest complete example. The schema is the `interface_defs:` section of `builder/base/config/schema.yaml`.

## Entry layout

The entry key is the interface type name. The sections are:

- `timing:` is required, `fixed` or `elastic`.
  - `fixed` means the receiver reads each value in a set cycle and cannot wait. `status` and `raw` sample a free-running bus, and `memory` returns read data one cycle after the request. `status`, `memory`, `raw` and `external_reg` are fixed, and their channel classes ignore `setTimed`.
  - `elastic` means a handshake paces each transfer, so idle cycles change only timing. Every handshake protocol is elastic.
- `backpressure:` is `{ default: <bool>, overridable: <bool> }`, declared exactly when `timing: elastic`. `default` says whether the consumer may stall the producer. `overridable: true` lets an `interfaces:` entry or a `ports:` row turn backpressure off, for a protocol whose handshake a design may leave unused. A design can only lower the default, so `overridable: true` is useful only with `default: true`. `rdy_vld` and `axi4_stream` are overridable. `apb`, `axi_read`, `axi_write`, `push_ack`, `pop_ack`, `req_ack` and `notify_ack` are not, because their consumer drives the ready or ack signal and can always stall. An elastic channel takes a delay only when every port it joins has backpressure on.
- `parameters:` lists the payloads the interface carries, in declaration order. An `interfaces:` entry binds each one by name through `structureType:` in its `structures:` list. Each parameter declares a `datatype:`:
  - `struct` binds a `structures` row and is one C++ template argument.
  - `type` binds a `types` row and is two template arguments, the name and the width. `axi_read` declares `id_t` this way.
  - `typeStruct` binds either kind and is also two arguments.

  `optional: true` lets a declaring interface leave the payload unbound. `defaultWidth:` (default 1) is the width of the signals an unbound optional parameter types. A protocol with no payload writes `parameters: {}` or omits the section.
- `hdlparams:` lists widths derived from a bound payload. Each entry declares `datatype: integer`, `isEval: true`, and a `value:` of the form `<parameter>.<expression>`, such as `data_t.to_bytes()`.
- `signals:` maps each wire to its type: a `parameters:` entry, an `isEval` `hdlparams:` entry, `bool`, or a type in scope of the definition's file or the system YAML. The shipped AXI and external_reg signals name `_axi*` and `_extRegWriteT` types this way. Flattened boundary ports follow this order.
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
- `uvmAgent: true` says the type ships a UVM agent and an X/Z checker, described under "UVM agent and X/Z checker" below. A `hasUvm` block may use only flagged types on its boundary, and `make db` names the port and type that break this. The HDL wrapper of every `hasVl` block, `hasUvm` or not, instantiates the checker on each port of a flagged type. `rdy_vld`, `apb`, `axi4_stream`, `raw` and `status` carry the flag.

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

The channel class carries the interface type's timing. Every class that constructs `interfaceBase` passes a required `timedDelayRule`. Both enums, `timedDelayRule` and `channelBackpressure`, are in `common/systemc/interfaceBase.h`.

- A fixed interface type's channel passes `TIMED_DELAY_FIXED_TIMING`, as `status_channel` does, and ignores `setTimed`.
- An elastic, non-overridable interface type's channel takes no constructor argument. It passes `TIMED_DELAY_APPLIES` when the default is backpressure on, and `TIMED_DELAY_NO_BACKPRESSURE` when it is off.
- An elastic, overridable interface type's channel takes a required `channelBackpressure` constructor argument after the block name, because the generator passes `BACKPRESSURE_ALLOWED` or `BACKPRESSURE_NONE` to every channel it builds for that type. It maps `BACKPRESSURE_NONE` to `TIMED_DELAY_NO_BACKPRESSURE` and `BACKPRESSURE_ALLOWED` to `TIMED_DELAY_APPLIES`.
- A composite channel built on `rdy_vld` sub-channels passes them the value. An overridable one forwards its own argument, as `axi4_stream_channel` does. A non-overridable one passes the literal `BACKPRESSURE_ALLOWED` or `BACKPRESSURE_NONE` that matches its default, as `axi_read_channel` does.
- A thunker of an overridable interface type takes the same `channelBackpressure` argument and passes it to its owned channel.

The generator spells a thunker as `<type>_port_thunker<up required payloads, down required payloads, one bool per required payload, up optional payloads, down optional payloads>`, each group in declaration order. Declare one `bool` per required parameter, defaulted to `false`, in that position, and pass it to `copyPayload<Flag>` at every copy site of that payload. `true` means the two sides emit identical member storage, so the payload is copied whole. `interfaces/rdy_vld/rdy_vld_port_thunker.h` is the smallest example. A protocol with no parameters, such as `notify_ack`, needs no thunker.

Every shipped definition sets `sc_channel.type` equal to its key. Keep them equal. A definition that points `sc_channel.type` at another protocol mixes two sets of names.

## UVM agent and X/Z checker

A definition with `uvmAgent: true` ships two more files beside it and adds a line to two file lists. For key `myproto`:

| File or entry | Contents |
| :--- | :--- |
| `myproto_uvm_pkg.sv` | package `myproto_uvm_pkg` with class `myproto_agent`, which exports the typedefs `item_t` and `config_t` |
| a line in `common/systemVerilog/uvm/a2c_uvm.f` | the package's path, after `a2c_clk_if.sv` and `a2c_uvm_pkg.sv`. Every agent imports `a2c_uvm_pkg` and reaches the clock through a `virtual a2c_clk_if`, so both come first. The simulators compile the agents from this list |
| `myproto_xcheck.sv` | exactly one module, `myproto_xcheck` |
| a `-y` line in `common/systemVerilog/a2c.f` | the definition's directory. Xcelium finds the checker through it, by file name. VCS ignores `-y` and analyses every `interfaces/*/*_xcheck.sv` through the wildcard in `VCS_LIB_SV_FILES` (`include/make/a2c-vcs.mk`) |

`interfaces/rdy_vld/rdy_vld_uvm_pkg.sv` and `interfaces/rdy_vld/rdy_vld_xcheck.sv` are the smallest complete pair.

### The agent package

- The agent's type parameters are the definition's `parameters:`, under the same names: `data_t` for `rdy_vld`, `addr_t` and `data_t` for `apb`, `tdata_t`, `tid_t`, `tdest_t` and `tuser_t` for `axi4_stream`. The generated variant package writes `typedef myproto_agent #(.<parameter>(<type>), ...) <port>_agent_t;` with the port's bound parameters only, and the same list on `virtual myproto_if`. An unbound optional parameter keeps the class default, so give it the default `myproto_if.sv` gives it.
- An agent that can play either side of the interface takes a role, `a2c_role_e` from `a2c_uvm_pkg`, in its config. The role is the opposite of the DUT port's modport, so a DUT `dst` port gets an `A2C_SRC` agent. `rdy_vld`, `axi4_stream`, `raw` and `status` take one. `apb_config` has no role, and the apb agent has only a master driver.
- Drivers drive at `clk_vif.drive_edge()` and monitors sample at `clk_vif.sample_edge()`, both defined in `common/systemVerilog/uvm/a2c_clk_if.sv`. Each monitor logs every transaction through `a2c_txn()` with id `A2C_TXN`.
- Add a test to `common/systemVerilog/uvm/loopback/a2c_uvm_loopback_tb.sv` and its name to `TESTS` in `run_loopback.sh`. The loopback runs on Xcelium and VCS only, as `run_loopback.sh xcelium|vcs [seed]`.

The test does not check the agent's content. A wrong class name or typedef passes `make db` and `make gen` and fails when a simulator compiles the UVM testbench.

### The X/Z checker

The HDL wrapper's boundary pins are two-state `bit`, so an X the RTL drives reaches SystemC as 0 and the run passes. The checker sits inside the SV wrapper, on the four-state interface the wrapper rebuilds from the pins, and fails the run on the first X or Z. Its rules:

- **Ports.** `input logic clk, input logic rst_n, myproto_if intf`. The wrapper connects the port's own domain clock and reset and the rebuilt interface instance.
- **Shared body.** `` `include "a2c_xcheck.svh" `` after the port list. It declares the DPI import, the arming process, `xzCheckEnabled()` and `xzFail(signal)`.
- **Sampling.** One `always @(negedge clk)` block, guarded by `xzCheckEnabled()`, with one `if`/`else if` chain that calls `xzFail("<signal>")` for the first unknown signal it finds.
- **Control signals are always checked.** For `rdy_vld` that is `vld` and `rdy`, for `axi4_stream` `tvalid` and `tready`, for `apb` `psel`, `penable` and `pready`.
- **Payload is checked only while the protocol's valid signals say it is defined.** `rdy_vld` checks `data` while `vld` is high, and `axi4_stream` checks every other signal while `tvalid` is high. `apb` checks `paddr` and `pwrite` while `psel` is high, and `pwdata` while `psel && pwrite`, because a read leaves it undefined. The completing cycle, `psel && penable && pready`, qualifies `pslverr`, and `prdata` on a read. `raw` and `status` have no qualifier, so their checkers test `data` on every clock.
- **Arming.** Checking starts once reset has been asserted and released. The HDL wrapper starts with reset released, and the DUT's outputs are X until its first reset. The checker arms when it starts with `rst_n` at 0, or on a falling edge of `rst_n` that does not end at X or Z, so a power-on X never arms it. It watches reset rather than a clock edge, because the socket lockstep wrapper can assert and release reset in delta cycles at time 0. It checks only while `rst_n === 1`, so a later reset pauses the check.
- **Reporting.** Each instance reports once, on its first X or Z. `xzFail` prints `A2C_XZ <time> <path>: <signal> is X or Z` and calls the DPI function `a2c_xz_fail` in `common/systemc/xzCheck.cpp`, which calls `errorCode::fail` with an `A2C_XZ` line. The run then exits non-zero. Base does not scaffold a rule for that. By convention each project's `rundir/default.json` carries an `exit_code` filter, and that filter fails the run on both vendors.
- **Four-state simulators only.** The wrapper places the instances inside `` `ifndef VERILATOR ``, because Verilator is two-state. Verilator builds still compile `xzCheck.cpp`, from the `common/systemc` wildcard, and never call it.

A src block leaves the placeholder signals of an unbound optional payload undriven, and the checker never checks them. For each signal typed by an optional parameter, the wrapper template passes `CHECK_<SIGNAL>`, the signal name in upper case, set to `1'b1` when the port binds that parameter and `1'b0` when it does not. The template reads the optional parameters from `getIntfParamBindings`, so it names no type. Declare `parameter bit CHECK_<SIGNAL> = 1'b0` for each such signal and test it before checking the signal, so a checker instantiated without the parameter never fails on a placeholder. `axi4_stream`'s `tuser`, typed by the optional `tuser_t`, is the only shipped case. `tid_t` and `tdest_t` are required, and `tstrb` and `tkeep` take their width from `tdata_t`, so the checker always tests those signals under `tvalid`.

### raw has limited UVM support

`raw` keeps `uvmAgent: true`, with limited support. Against the RTL DUT support is complete, because the agent drives and samples the pins on every clock. Against the model DUT it is best effort, because `raw_src_bfm` is not transactional. The BFM blocks in `if_p->write()`, and a word presented while it blocks is lost. It counts each clock edge whose word SystemC did not take, from the reader's first read on, and reports the count through `bfmContractCheck`, as one line at the first miss and the total at the end of simulation. That is a warning and never `errorCode::fail`. The note is in the header of `interfaces/raw/raw_uvm_pkg.sv`.

### What the test enforces

`builder/base/unittest/test_uvm_agent_companions.py` walks every definition under `builder/base/interfaces/` and `builder/pro/interfaces/` and finds the flagged ones, so it checks a newly flagged type without anyone adding it to a list. For each, it checks that:

1. `<type>_uvm_pkg.sv` exists beside the definition;
2. `a2c_uvm.f` lists that package, and lists `a2c_clk_if.sv` and `a2c_uvm_pkg.sv` before every agent package;
3. `<type>_xcheck.sv` exists beside the definition, declares exactly one module, `<type>_xcheck`, and sits in a directory that a `-y` line of `a2c.f` names.

It fails when it finds no flagged definition at all. Run it after you flag a type or move its files:

```bash
python3 builder/base/unittest/test_uvm_agent_companions.py
```

The test checks names and places, not behaviour. `common/systemVerilog/xcheck_test/` checks behaviour. Its `run_xcheck_test.sh xcelium|vcs` builds `xcheck_tb.sv` with the checkers, and `xz_count.c` stands in for `a2c_xz_fail` and counts each checker's reports. Its 46 cases cover each shipped type. For a new type, add it to `TYPES` in the script, add its cases to `xcheck_tb.sv` and raise `CASES`. Verilator cannot run it.

A Pro definition cannot carry the flag today. `a2c.f` has no `-y` line for `builder/pro/interfaces`, so the test fails, and the VCS wildcard does not reach Pro either.

## Declaration rules

The schema enforces rule 5 and a missing `timing:`, so either stops `make db`. `builder/base/unittest/test_interface_def_contracts.py` checks the other rules over every definition under `builder/base/interfaces/` and `builder/pro/interfaces/`. Run it after you edit a shipped definition:

```bash
python3 builder/base/unittest/test_interface_def_contracts.py
```

1. **Optional parameters come last.** Declare every `optional: true` parameter after every required one. The generator builds the BFM and thunker signatures by splitting the parameter list at its first optional parameter and splicing another argument group between the halves. A required parameter after an optional one lands in the wrong argument slot, and generation still succeeds.
2. **An `isEval` hdlparam evaluates a required `struct` parameter.** The signal it types is always declared, so its width must always exist. An unbound optional parameter has no width, and generation fails for an interface that leaves it unbound. The parameter must be a `struct` because, for a parameterizable payload, the SystemC bridge spells the width as `S<Config>::_byteWidth`, and only a generated structure declares `_byteWidth`.
3. **Every modport lists every signal.** The generator makes a signal an input when it is in the modport's `inputs:` and an output otherwise. A signal missing from a modport becomes an output, the wrapper drives it backwards, and generation still succeeds.
4. **An `isEval` `value:` calls one method on one parameter.** The generator evaluates the value with each parameter name bound to an object that measures that payload, and with no Python builtins, so `<parameter>.to_bytes()` is the only shape it can evaluate. Any other shape stops generation with a bare Python error that names neither the interface nor its file.
5. **Every parameter declares `datatype:` as `struct`, `type` or `typeStruct`.** Any other value fails the schema check.
6. **Only an optional parameter sets `defaultWidth:` other than 1.** A required parameter is always bound, so the generator never reads its `defaultWidth`, and the value misleads the reader.
7. **Every signal type resolves to a width.** A signal's type must be `bool`, a parameter, an `isEval` hdlparam, or a type in scope. The SV boundary port and the simulator boundary pin both take their width from it, so a literal SV spelling such as `bit [7:0]` leaves the pin with no width.
8. **Every `isEval` hdlparam types at least one signal.** The Verilated bridge takes one type per `isEval` hdlparam and reads it from a signal of that type. An `isEval` hdlparam that types no signal stops generation with a bare `KeyError` that names neither the interface nor its file.
9. **`backpressure:` is declared exactly when `timing: elastic`.** A fixed interface has no handshake to stall, so a group there misleads the reader. An elastic definition without one stops generation with a bare `TypeError` at the first channel or port of that type. The schema requires `timing:` and both group fields, but not the pairing.

The schema check covers a project-local definition, so rule 5 applies to it. The test walks only the shipped trees, so check a project-local definition against rules 1 to 4 and 6 to 9 by hand.
