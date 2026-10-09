---
name: rtl-core
description: Guide for writing core RTL modules in SystemVerilog including module structure, FSMs, reset logic, flip-flop macros, clock domains, naming conventions, and coding idioms
---
# Skill: RTL core

## Purpose
Write the hand-written SystemVerilog of an arch2code block: module structure, flop macros and clock domains, FSMs, naming and coding idioms. Other RTL skills link here for the flop macros, the `clk`/`rst_n` aliases and FSMs.

## References
*   `ARCH2CODE_AI_RULES.md`, section "Code Generation Markers", lists every `GENERATED_CODE_PARAM` and `GENERATED_CODE_BEGIN` option.

## Instructions

### 1. Module structure

*   The generator writes the module declaration, ports, package imports, interface instances, child instances and memory instances. Never edit between `// GENERATED_CODE_BEGIN` and `// GENERATED_CODE_END`.
*   Put your logic after `// GENERATED_CODE_END`. End the module with `endmodule: <module_name>`.
*   A module or package is named like its file: the block name, or `<includeName>_package` for a YAML context, with the owning project's `svFilePrefix` in front. Names are not otherwise project-qualified, so two projects that emit the same name collide, and `make db` rejects it.
*   Parameterizable types, enums, structures and derived constants are not in the package. The generated region declares them inside the module, from the module's parameters.
*   Ports come in this order: interface ports, then the block's clocks, then its resets, each in declaration order. A block with no `clocks:` gets an input `clk`. A block with no `resets:` gets an input `rst_n` on its default clock. `resets: {}` gives no reset port at all.
*   The generated region imports the package of each YAML context whose types or constants the generated code uses. That includes the types on the block's ports, interface instances, registers, memories and parameterized type declarations. It also includes the constants that child-instance parameter bindings name, and the context of each parameterizable child. The block's own context is imported only when one of these uses it.
*   Never write a package import by hand. If your logic names a type or constant from a package the region does not import, add the package with `--importPackages` on the `GENERATED_CODE_PARAM` line. List every package after one flag, as in `--importPackages a_package b_package`. The generator reads only the first flag.

```systemverilog
// GENERATED_CODE_PARAM --block=twoClkSlowTick
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
module twoClkSlowTick
import twoClkIp_package::*;
(
    push_ack_if.src out,
    input clkTick, rstTick_n
);
    // Default-domain aliases: the bare flop macros expand to clk / rst_n
    wire clk = clkTick;
    wire rst_n = rstTick_n;
// GENERATED_CODE_END

    // your logic here

endmodule: twoClkSlowTick
```

### 2. Clock domains and the `clk`/`rst_n` aliases

Every block with an input clock has `clk` for its default domain, and `rst_n` when the default clock has a selected reset. They are either ports, or the generated region declares them as aliases (`wire clk = <default clock>;` and `wire rst_n = <its selected reset>;`), as above. The generator skips an alias when a declared port already has that name. The bare flop macros, the Pro FSM macros and `.*` therefore bind the default domain whatever its ports are called.

The aliases are missing, or name the wrong signal, in these cases:
*   The block has no input clock. There is no `clk` alias, and a declared output clock named `clk` is what the bare macros use.
*   The default clock has no selected synchronous reset: `resets: {}`, every reset `async: true`, or every reset on another clock. There is no `rst_n` alias, and a declared reset named `rst_n` is used as is.
*   A declared clock named `clk` is not the default clock, or a declared reset named `rst_n` is not the default clock's selected reset (for example an `async: true` `rst_n`). The bare macros then use that clock or reset.

In the first and third cases, name the clock and reset with the `_DOM` macros and bind library instances explicitly. In the second case there is no synchronous reset to name. Use the no-reset macros (`DFFNR`, `DFFNR_INST`), or add a reset synchroniser on the default clock, whose output then becomes the selected reset and the `rst_n` alias.

Pick the macro form by the flop's clock:

| Flop's clock | Form | Example |
| :--- | :--- | :--- |
| Default clock | Bare | `` `DFF_INST(logic, busy) `` |
| Any other clock | `_DOM`, clock and reset given | `` `DFF_INST_DOM(clkSlow, rstSlow_n, logic, busy) `` |
| Another clock that shares `rst_n`, where `rst_n` is safe to use in that domain | `_CLK` is allowed | `` `DFF_INST_CLK(clkFast, logic, busy) `` |

`_CLK` always resets on `rst_n`. In the table, `clkFast` shares `rst_n`, so `_CLK` is correct there. On a clock that has its own reset, `_CLK` puts the flop in the wrong reset domain, so use `_DOM`. When in doubt, use `_DOM`.

A library instance (A2C Pro `memArb`, `rdyVldFifo` and so on) on another clock binds that clock and its own reset explicitly, `.clk(clkSlow), .rst_n(rstSlow_n)`, instead of relying on `.*`.

### 3. Flop macros

Never write `always_ff` directly. The one exception is a reset supplier's assertion path, such as a reset synchroniser's asynchronous input flop or a PLL wrapper's raw output reset. Write those with explicit asynchronous flops so the domain resets while its clock is stopped.

The macros live in `flops.sv`. Each family has a bare, a `_CLK` and a `_DOM` form:
*   `_DOM` takes the clock and the reset as its first two arguments, and holds the only flop body.
*   `_CLK` takes the clock as its first argument and passes `rst_n` to `_DOM`.
*   Bare passes `clk` to `_CLK`.

| Bare macro | Behaviour | Declares |
| :--- | :--- | :--- |
| `` `DFF_INST(type, name) `` | Resets to `'0` | `type name, n_name;` |
| `` `DFFR_INST(type, name, rval) `` | Resets to `rval` | `type name, n_name;` |
| `` `DFFNR_INST(type, name) `` | No reset | `type name, n_name;` |
| `` `DFFEN_INST(type, name, en) `` | Loads when `en`, resets to `'0` | `type name, n_name;` |
| `` `DFF_KEEP_INST(type, name) `` | As `DFF_INST`, kept by synthesis | `type name, n_name;` |
| `` `DFFR_KEEP_INST(type, name, rval) `` | As `DFFR_INST`, kept by synthesis | `type name, n_name;` |
| `` `DFF(q, d) `` | Resets to `'0` | nothing |
| `` `DFFR(q, d, rval) `` | Resets to `rval` | nothing |
| `` `DFFNR(q, d) `` | No reset | nothing |
| `` `DFFEN(q, d, en) `` | Loads when `en`, resets to `'0` | nothing |
| `` `DFFREN(q, d, en, rval) `` | Loads when `en`, resets to `rval` | nothing |
| `` `SCFF(q, s, c) `` | Set-clear flop, set wins | nothing |

There is no `DFFREN_INST` or `SCFF_INST`. For those, declare the signals and use the raw macro.

The other forms add arguments at the front: `` `DFFR_INST_DOM(clkSlow, rstSlow_n, cntT, count, '0) ``, `` `DFFEN_DOM(clkSlow, rstSlow_n, q, d, en) ``, `` `SCFF_DOM(clkSlow, rstSlow_n, q, s, c) ``.

The KEEP macros add Synplify's `syn_keep` and `syn_preserve` attributes, so Synplify does not merge the register with an equivalent one. Other synthesis tools need their own attribute.

```systemverilog
`DFF_INST(logic, stg1Vld)
`DFFR_INST(countT, credits, MAX_CREDITS)

always_comb begin
    n_stg1Vld = inPort.vld;
    n_credits = credits;
    if (consume) begin
        n_credits = credits - 1'b1;
    end
end
```

### 4. Reset style

`flops.sv` builds every flop in one of three styles. Exactly one is active per compilation:
*   `A2C_RESET_SYNC`, the default. Synchronous active-low reset.
*   `A2C_RESET_ASYNC`. Asynchronous active-low reset on the flop's sensitivity list.
*   `A2C_RESET_NONE`. No reset. An `initial` statement sets the start value, for FPGA images.

`ASIC` is an alias for `A2C_RESET_SYNC` and `FPGA_INIT_FLOPS` for `A2C_RESET_NONE`. Defining two styles fails to compile. Select a style with a define, for example `make lint VERILATOR_USER_OPTS=+define+A2C_RESET_ASYNC`, or the same define in your synthesis tool. Write RTL the same way for every style.

### 5. Finite state machines

Every project can write an FSM as a plain `case` with the state in a flop macro:

```systemverilog
typedef enum logic [1:0] {RDY, WORK, DONE} fsmStateT;
`DFFR_INST(fsmStateT, state, RDY)

always_comb begin
    n_state = state;
    outVld = 1'b0;
    case (state)
        RDY: begin
            if (start) begin
                n_state = WORK;
            end
        end
        WORK: begin
            outVld = 1'b1;
            if (outAck) begin
                n_state = DONE;
            end
        end
        DONE: begin
            n_state = RDY;
        end
        default: `qAssertFatal(0, "Default clause should not be reached")
    endcase
end
```

For an FSM on a non-default clock, declare the state with `DFFR_INST_DOM`.

**A2C Pro FSM macros.** `fsmDefs.svh` ships only with A2C Pro (`builder/pro/common/systemVerilog`, on the Verilator path through `a2cPro.f`). It runs on the default domain only.
*   Name the enum `statesT`. The include derives `stateT`, declares `state` and `nState`, and adds the state flop, reset to the first enum value. Do not declare `state` or `nState` yourself.
*   Define `QS_ONEHOT_FSM` for one-hot encoding. The default is encoded.
*   `` `pushState(ST) `` and `` `popState `` use `pushState` and `nPushState`, which the include does not declare. Declare `stateT pushState, nPushState;`, flop them with `` `DFFR(pushState, nPushState, <a valid state>) ``, and default `nPushState = pushState;` in the `always_comb`. The reset value must be a state in the FSM's encoding. When encoded, use a state name such as `RDY`. Under `QS_ONEHOT_FSM`, use a one-hot value such as `stateT'(1)`, the first state. `stateT'(0)` is no state there.

```systemverilog
typedef enum logic [1:0] {RDY, WORK, DONE} statesT;
`include "fsmDefs.svh"

always_comb begin
    nState = state;
    outVld = 1'b0;
    `fsmCase
        `fsmState(RDY) begin
            if (start) begin
                `nxtState(WORK)
            end
        end
        `fsmState(WORK) begin
            outVld = 1'b1;
            if (outAck) begin
                `nxtState(DONE)
            end
        end
        `fsmState(DONE) begin
            `nxtState(RDY)
        end
        default: `qAssertFatal(0, "Default clause should not be reached")
    `fsmEndCase
end
```

`` `testState(ST) `` tests the current state.

For several FSMs in one module, scope each one in `if (1) begin: gen_<fsm> ... end: gen_<fsm>`. Each scope then has its own enum, `state` and `n_state` (or `nState`).

### 6. Combinational logic

*   Use `always_comb`, one per logical section such as a pipeline stage.
*   Assign every driven signal a default at the top of the block (`n_x = x;`, `out = '0;`), then override it in branches. This prevents latches.
*   Use `begin`/`end` on every branch.
*   Declare combinational intermediates at module scope and drive them in `always_comb`. They cost no flops.

### 7. Assertions

`asserts.svh` defines three macros:
*   `` `qAssertFatal(cond, "msg") `` stops the simulation.
*   `` `qAssertError(cond, "msg") `` reports an error. The simulator decides whether to stop.
*   `` `qAssertWarning(cond, "msg") `` reports a warning.

The macros expand to immediate assertions, so place them inside a procedural block:

```systemverilog
always_comb begin
    `qAssertError(count <= MAX_COUNT, "Counter overflow")
end
```

### 8. Naming

| Element | Convention | Example |
| :--- | :--- | :--- |
| Modules, ports, instances, YAML types and constants | Generated. Keep the YAML spelling. | `twoClkTable`, `uTwoClkTableRegs`, `twoClkDataT`, `TWO_CLK_TICK_DIV` |
| Hand-written signals | camelCase, as in the examples and the Pro library | `sweepAddr`, `statsValid` |
| `localparam` constants | `UPPER_SNAKE_CASE` | `EXTA_SEED` |
| Local types | camelCase, `T` suffix, or `St` for a struct | `fsmStateT`, `lutEntrySt` |
| Enum values | `UPPER_SNAKE_CASE` | `RDY`, `WORK` |
| Next state of an `_INST` flop | `n_<name>`, declared by the macro | `n_sweepAddr` |
| Next state for a raw macro | `nxt_<name>`, declared by you | `nxt_rdData` |
| Generate blocks | `gen_<desc>` label | `gen_lane` |

Keep one style within a module. A module written in snake_case stays in snake_case.

The A2C Pro FSM macros require the names `state`, `nState`, `pushState` and `nPushState`. They are exempt from the `n_` and `nxt_` rules.

### 9. Idioms

*   Use `logic` for everything you declare. `wire` appears only in the generated region, for the `clk`/`rst_n` aliases and for clock and reset nets a child instance drives.
*   Use `'0` and `'1` for all-zeros and all-ones.
*   Mark functions and procedural loop variables `automatic`.
*   Detect overflow with a reduction OR, `|accum[MSB:DATA_WIDTH]`.
*   Cast with the type: `addrT'(busAddr)`, `$signed({1'b0, uval})` to zero-extend into a signed value.
*   Waive an intentional width mismatch around the expression only: `/* verilator lint_off WIDTHTRUNC */ ... /* verilator lint_on WIDTHTRUNC */`.
*   Carry `vld` and sideband data through every pipeline stage.
*   Tie `in.rdy = 1'b1` only when the block can accept every cycle. Otherwise derive `rdy` from downstream, as in `rtl-interfaces.md`.
