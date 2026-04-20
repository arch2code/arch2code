---
name: review-rtl
description: Checklist-driven review of SystemVerilog RTL for arch2code conventions, industry best practices, FUSA, and model-RTL conformity, with awareness of tandem mode's role
globs: "rtl/**/*.sv, rtl/**/*.svh"
alwaysApply: false
---
# Skill: Review RTL

## Purpose
Perform a structured code review of a SystemVerilog RTL module within the arch2code framework. The review covers framework conventions, industry best practices, functional safety (FUSA), and lightweight model-RTL conformity checks.

**Tandem mode context:** In this framework, RTL is verified against a SystemC golden model via tandem mode (see `run-tandem.md`). Tandem mode proves functional equivalence at interface boundaries by running both implementations in lockstep and comparing every transaction. This fundamentally affects the code review approach -- many checks that would traditionally require RTL-side assertions or formal properties are instead caught by tandem mode. The reviewer must understand this tradeoff and not flag the *absence* of certain assertions as a defect when tandem mode covers them.

## References
*   **RTL Conventions:** `rtl-core.md` (Module structure, FSMs, DFF macros, naming)
*   **RTL Patterns:** `rtl-patterns.md` (Pipelines, saturation, resource sharing)
*   **RTL Interfaces:** `rtl-interfaces.md` (Port protocols)
*   **RTL Registers:** `rtl-registers.md` (Decoder, external regs)
*   **Tandem:** `run-tandem.md` (Build/run tandem verification)
*   **Co-Simulation:** `verify-cosimulation.md` (Verilator wrapper setup)
*   **SC->RTL Conversion:** `systemc-to-rtl.md` (Conversion patterns)

## Understanding Tandem Mode's Impact on Review

Before reviewing, understand how tandem mode affects what to look for:

1.  **Assertions are often intentionally sparse in RTL.** Tandem mode catches functional mismatches (wrong output values, wrong transaction ordering, missing transactions) by comparing RTL outputs against the model. Adding redundant `qAssert` checks for conditions that tandem already covers adds simulation overhead without additional safety. Only flag missing assertions when they guard structural invariants that tandem cannot observe (e.g., internal FSM illegal states, FIFO pointer corruption).

2.  **Algorithmic correctness is not the reviewer's burden.** If the math, rounding, or saturation logic produces wrong results, tandem mode will catch it. The reviewer should focus on whether the RTL is *well-structured* and *synthesizable*, not whether the algorithm is correct.

3.  **Interface-level behavior is the contract.** Tandem mode compares at interface boundaries (`rdy_vld_if`, `memory_if`, `status_if`). Internal pipeline structure, number of stages, and intermediate signal values are implementation details -- they only matter if they affect the interface contract.

4.  **Where assertions ARE still needed:**
    *   FSM `default:` clauses with `qAssertFatal` -- these catch illegal states that could cause the RTL to lock up silently (tandem would hang rather than report the root cause).
    *   Structural invariants: FIFO pointer wrap-around, counter overflow where the counter controls interface behavior, arbiter grant conflicts.
    *   Conditions that would cause simulation divergence rather than a clean mismatch (e.g., X-propagation in Verilator).

## Instructions

### 1. Arch2code Convention Checks

*   **Generated Code Zones:** Verify no manual edits exist between `// GENERATED_CODE_BEGIN` and `// GENERATED_CODE_END` markers.
*   **DFF Macros:** All sequential logic uses `DFF_INST`, `DFFR_INST`, `DFFNR_INST`, `DFFEN_INST`, or the raw variants (`DFF`, `DFFR`, `DFFNR`, `DFFEN`, `DFFREN`, `SCFF`). No raw `always_ff` blocks.
*   **FSM Macros:** All state machines use `fsmDefs.svh` macros (`fsmCase`, `fsmState`, `nxtState`, `fsmEndCase`). The enum type is named `statesT`. Multiple FSMs use `if (1) begin: <label>` scoping.
*   **Naming Conventions:** Verify against `rtl-core.md` table:
    *   Modules: `snake_case`. Instances: `u_<name>`.
    *   Constants: `UPPER_SNAKE_CASE`. Types: `snake_case_t`.
    *   Next-state (`_INST` macros): `n_<name>`. Next-state (raw macros): `nxt_<name>`.
    *   Pipeline stages: `stgN_` or `sN_` prefix. Generate blocks: `gen_<desc>` label.
*   **Type Usage:** All signals declared with `logic`. No `reg` or `wire`.
*   **Module End Label:** Module ends with `endmodule: <module_name>`.
*   **Package Imports:** Block package imported via `import <block>_package::*;`.

### 2. Industry Best Practice Checks

*   **No Inferred Latches:** Every `always_comb` block assigns default values at the top for all driven signals.
*   **Combinational Only:** All procedural logic uses `always_comb`. No `always @*` or `always @(posedge ...)` outside of macros.
*   **Width Matching:** Expressions have matching bit-widths, or intentional mismatches are guarded by Verilator lint pragmas (`WIDTHTRUNC`, `WIDTHEXPAND`).
*   **No X/Z Propagation Risks:** Reset values are explicit. Uninitialized signals do not propagate to outputs.
*   **Parameterized Constants:** No magic numbers in logic. Use `localparam` or package constants.
*   **No Combinational Loops:** No signal driven by an `always_comb` block that also reads itself without a flop in the path.
*   **Functions:** Use `automatic` keyword. No side effects.
*   **Generate Blocks:** All generate blocks have `gen_<desc>` labels. Use `genvar` for generate loops, `int` for procedural loops.

### 3. Functional Safety (FUSA) Checks

*   **Reset Coverage:** Every flop has a defined reset value via `DFF_INST` (resets to `'0`), `DFFR_INST` (explicit value), or `DFFEN_INST`. Use of `DFFNR_INST` (no reset) must be justified (e.g., datapath-only, non-safety-critical).
*   **FSM Default Clauses:** Every FSM has a `default:` case with `` `qAssertFatal(0, "...") ``. This is required even though tandem mode catches functional mismatches -- a silent illegal state causes hangs that are hard to diagnose.
*   **No Unreachable States:** FSM state encoding has no unused states, or unused states transition to a known-good state.
*   **Structural Assertions Only:** Assertions (`qAssert`/`qAssertFatal`) should guard structural invariants that tandem mode cannot directly observe:
    *   FIFO pointer corruption or overflow.
    *   Arbiter grant conflicts (multiple simultaneous grants).
    *   Counter overflow where the counter controls flow (e.g., credit counters).
    *   Do **not** flag the absence of assertions for algorithmic checks (e.g., "output value in range") -- tandem mode covers these.
*   **Error Propagation:** Error signals from sub-blocks propagate to the module's outputs or are handled (not silently dropped).
*   **Deterministic Behavior:** No reliance on undefined evaluation order. No race conditions between combinational assignments.

### 4. Model-RTL Conformity Checks

*   **Read the Model:** Open the corresponding `model/<block>.cpp` alongside the RTL.
*   **Naming Consistency:** RTL signal names should be recognizable counterparts of model variable names (e.g., model `pos_x` maps to RTL `pos_x`, model `gain_factor` maps to RTL `gain_factor`).
*   **Type/Width Alignment:** RTL `logic [N:0]` and struct types should correspond to the model's C++ types without silent truncation or sign mismatch.
*   **Scope:** Functional equivalence (algorithm correctness, rounding behavior, transaction ordering) is proven by tandem mode. Do not duplicate that verification here.

### 5. Review Output Format

Present findings as a checklist. For each category, report:

```
## <Category Name>
- [PASS] <item description>
- [FAIL] <item description> -- <explanation and suggested fix>
- [WARN] <item description> -- <note or recommendation>
- [N/A]  <item description> -- <reason not applicable>
```

Summarize with a count: `X PASS, Y FAIL, Z WARN, W N/A`.

## Constraints
*   This review is for **RTL code only** (`rtl/**/*.sv`). For model code, use the **review-model** skill.
*   Do not modify generated code zones.
*   Do not flag missing algorithmic assertions -- tandem mode proves functional equivalence.
*   Flag items as `[WARN]` rather than `[FAIL]` when the issue is stylistic rather than functional.
