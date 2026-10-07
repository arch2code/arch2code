---
name: review-rtl
description: Checklist-driven review of SystemVerilog RTL for arch2code conventions, industry best practices, FUSA, and model-RTL conformity, with awareness of tandem mode's role
---
# Skill: Review RTL

## Purpose
Review a hand-written SystemVerilog module for arch2code conventions, industry practice, functional safety (FUSA) and conformity with its SystemC model.

## References
*   `rtl-core.md` owns the rules this review checks: flop macros and clock domains, FSMs, naming, package imports and idioms. Judge against it, not against memory.
*   `rtl-interfaces.md`, `rtl-registers.md`, `rtl-patterns.md` and `systemc-to-rtl.md` cover interfaces, register ports, patterns and conversion.
*   `run-tandem.md` (A2C Pro) and `verify-cosimulation.md` cover tandem and co-simulation.

## How tandem changes the review
Tandem mode (A2C Pro) runs a leaf block's RTL and its SystemC model on the same stimulus and compares what each sends out. A mismatch on any interface except `status` fails the run. A `status` mismatch only warns unless the run sets `--tandemStatusFatal`. Tandem shows that model and RTL agree on that stimulus. It does not show either is correct, because a bug both share passes. Review with that in mind:

*   Review the algorithm independently: math, rounding, saturation, interpolation.
*   Treat the interface behaviour as the contract. Pipeline depth and internal signals matter only when they change it.
*   Do not ask for assertions on things tandem compares, such as "output value in range". Ask for them only on internal invariants tandem cannot see: illegal FSM states, FIFO pointer corruption, arbiter grant conflicts, and counters that control flow, such as credits.

## Instructions

### 1. Arch2code conventions

*   **Generated regions.** Nothing between `// GENERATED_CODE_BEGIN` and `// GENERATED_CODE_END` is hand-edited.
*   **Flops.** Every flop uses a macro from the `rtl-core.md` table, in its bare, `_CLK` or `_DOM` form. `always_ff` is allowed only on a reset supplier's assertion path.
*   **Flop clock and reset.** Check each flop's domain:
    *   A bare macro is correct for the default clock, whatever its port is called. The generated region aliases `clk` and `rst_n` onto it. Do not flag a bare macro because the clock port is not named `clk`.
    *   A flop on any other clock uses `_DOM` with that clock and its own reset. PASS.
    *   `_CLK` resets on `rst_n`. It is correct only on a clock that shares `rst_n`, where that reset is safe to use. FAIL `_CLK` on a clock that has its own reset.
    *   A library instance on a non-default clock binds `.clk` and `.rst_n` explicitly. FAIL one that relies on `.*` there.
    *   Check the cases in `rtl-core.md` where the aliases are missing or point elsewhere.
*   **FSMs.** The state is a flop macro. Either the plain `case` form or the A2C Pro `fsmDefs.svh` macros with the enum named `statesT` passes. Several FSMs in one module are each scoped with `if (1) begin: gen_<fsm> ... end: gen_<fsm>`.
*   **Naming.** Do not flag names generated from YAML: modules, ports, instances, YAML types and constants. Hand-written names follow `rtl-core.md` and stay consistent within the module. Report naming as WARN.
*   **Types.** Declare with `logic`, never `reg`. Prefer the generated package types to raw `logic [N:0]`. A local typedef is fine for an internal value with no package counterpart, such as an accumulator width derived from a `localparam`.
*   **Package imports.** FAIL any hand-written package import in a module. A package the generated region does not import comes through `--importPackages` on the `GENERATED_CODE_PARAM` line (`rtl-core.md`). Packages are per context, not per block, so `<block>_package` does not exist.
*   **Generated modules.** Do not review the generated register handler (`<block>_regs` by default, `<block>Regs` in the examples) or the router module, which is named after the router block. Review only the hand-written RTL.
*   **Module end.** The module ends with `endmodule: <module_name>`.

### 2. Industry practice

*   **No latches.** Every `always_comb` gives each driven signal a default at the top.
*   **Combinational logic.** Procedural logic is `always_comb`. No `always @*`.
*   **Widths.** Expressions match in width, or a Verilator `WIDTHTRUNC`/`WIDTHEXPAND` waiver covers an intended mismatch.
*   **X propagation.** Flops that reach an output or control state have a reset value. Uninitialized signals do not reach outputs.
*   **Magic numbers.** Flag numeric literals in logic, comparisons, slice bounds and shift amounts. Each should be a `localparam` or package constant. `'0`, `'1`, `1'b0`, `1'b1`, `+ 1'b1` and `32'hBADD_C0DE` are fine.
*   **Combinational loops.** No `always_comb` reads a signal it drives without a flop in between.
*   **Order inside `always_comb`.** No block reads a signal before the statement in the same block that assigns it. Verilator reports this as `ALWCOMBORDER`.
*   **Functions.** Functions are `automatic` and have no side effects.
*   **Generate blocks.** Each has a `gen_<desc>` label. Generate loops use `genvar`, procedural loops `int`.

### 3. Functional safety

*   **Reset coverage.** Every flop resets, except where a no-reset macro (`DFFNR`, `DFFNR_INST` and their variants) is justified, such as datapath storage that a valid bit qualifies.
*   **FSM default.** Every FSM `case` has a `default:` branch with `` `qAssertFatal(0, "...") ``. An illegal state otherwise hangs tandem without naming the cause.
*   **Unreachable states.** Unused state encodings either do not exist or go to a known state.
*   **Assertions.** Use `qAssertFatal`, `qAssertError` or `qAssertWarning` for the internal invariants listed under "How tandem changes the review". Do not flag a missing assertion that tandem covers.
*   **Error propagation.** Error signals from sub-blocks reach an output or are handled.
*   **Determinism.** Nothing depends on evaluation order between combinational blocks.

### 4. Model-RTL conformity

*   Read `model/<block>.cppm` next to the RTL.
*   RTL signal names are recognisable counterparts of the model's variables.
*   RTL types correspond to the model's C++ types. Flag silent truncation and sign mismatches.
*   Check the algorithm on its own merits, as described under "How tandem changes the review".

### 5. Output format

Report a checklist per category:

```
## <Category>
- [PASS] <item>
- [FAIL] <item>: <why, and the fix>
- [WARN] <item>: <note>
- [N/A]  <item>: <why it does not apply>
```

End with the counts: `X PASS, Y FAIL, Z WARN, W N/A`.

## Constraints
*   This review covers RTL only (`rtl/**/*.sv`). Use `review-model` for model code.
*   Do not modify generated regions.
*   Use WARN, not FAIL, for style issues that do not change behaviour.
