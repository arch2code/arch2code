---
name: rtl-core
description: Guide for writing core RTL modules in SystemVerilog including module structure, FSMs, reset logic, flip-flop macros, naming conventions, and coding idioms
globs: "rtl/**/*.sv, rtl/**/*.svh"
alwaysApply: false
---
# Skill: RTL Core

## Purpose
Guide the user in writing core RTL modules in SystemVerilog, focusing on module structure, FSMs, flip-flop macros, naming conventions, and coding idioms.

## Instructions

1.  **Module Structure & Generated Code:**
    *   **Auto-Generation:** The module declaration, interface ports, and package imports are **auto-generated** by `arch2code` based on the YAML definition.
    *   **Safe Zones:** **NEVER** modify code between `// GENERATED_CODE_BEGIN` and `// GENERATED_CODE_END` markers.
    *   **Implementation:** Place all manual logic (FSMs, internal signals, sub-module instances) after the generated sections.
    *   Module ends with `endmodule: <module_name>` (named end).
    *   `clk` and `rst_n` are always the last two ports. Active-low reset: `rst_n`.

    ```systemverilog
    // GENERATED_CODE_PARAM --block=<block_name>
    // GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
    module tagScheduler
        import NVMe_package::*;
        import sharedTop_package::*;
    (
        // Auto-generated ports from YAML connections
        input clk, rst_n
    );
    // ... generated instances ...
    // GENERATED_CODE_END

    // <--- Your code goes here --->

    endmodule: tagScheduler
    ```

2.  **Naming Conventions:**

    | Element | Convention | Example |
    |---------|------------|---------|
    | Modules | `snake_case` | `dma_engine`, `tag_scheduler` |
    | Instances | `u_<name>` | `u_dma_engine`, `u_tag_scheduler` |
    | Constants | `UPPER_SNAKE_CASE` | `MAX_BURST_LEN`, `DATA_WIDTH` |
    | Types | `snake_case_t` | `count_t`, `addr_t`, `accum_t` |
    | Structs | `snake_case_t` or `snake_case_st` | `cmd_entry_t`, `lut_entry_st` |
    | Enums | `UPPER_SNAKE_CASE` values | `IDLE`, `ACTIVE`, `DONE` |
    | Next-state (`_INST` macros) | `n_<name>` (auto-declared) | `n_stg1_valid`, `n_count` |
    | Next-state (raw macros) | `nxt_<name>` (manually declared) | `nxt_wr_ready`, `nxt_data` |
    | Pipeline stages | `stgN_` or `sN_` prefix | `stg1_valid`, `s2_data` |
    | Generate blocks | `gen_<desc>` label | `gen_mem_inst`, `gen_lane` |

3.  **Finite State Machines (FSMs):**
    *   **Use Macros:** Do NOT write raw `case` statements for state machines. Use `fsmDefs.svh` macros.
    *   **Critical:** The enum type **must** be named `statesT`. The include file references this name to derive `stateT`, declare `state`/`nState`, and instantiate the state flop. Do **not** declare `state` or `nState` yourself.
    *   **Pattern:** `always_comb` block with `nState = state;` default.

    ```systemverilog
    typedef enum logic [1:0] {RDY, WORK, DONE} statesT;
    `include "fsmDefs.svh"

    always_comb begin
        nState = state;
        out_vld = 1'b0;

        `fsmCase
            `fsmState(RDY) begin
                if (start) begin
                    `nxtState(WORK)
                end
            end

            `fsmState(WORK) begin
                out_vld = 1'b1;
                if (out_ack) begin
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

    **FSM Macros:**
    *   `` `fsmCase `` / `` `fsmEndCase ``: wraps case statement (supports encoded or one-hot via `QS_ONEHOT_FSM` define)
    *   `` `fsmState(ST) ``: case label for a state
    *   `` `nxtState(ST) ``: transition to next state
    *   `` `testState(ST) ``: test current state (returns logic)
    *   `` `pushState(ST) ``: save a state for later return
    *   `` `popState ``: restore previously pushed state

    **Scoped FSMs:** Use `if (1) begin: <label>` blocks for multiple FSMs in the same module, each with their own `statesT`:

    ```systemverilog
    if (1) begin: read_fsm
        typedef enum logic [1:0] {IDLE, REQ, WAIT, DONE} statesT;
        `include "fsmDefs.svh"
        always_comb begin /* ... */ end
    end: read_fsm

    if (1) begin: write_fsm
        typedef enum logic [1:0] {IDLE, BURST, RESP} statesT;
        `include "fsmDefs.svh"
        always_comb begin /* ... */ end
    end: write_fsm
    ```

4.  **Flip-Flop Macro System:**

    **Never write `always_ff` directly.** Use DFF macros instead.

    | Macro | Purpose | Creates |
    |-------|---------|---------|
    | `` `DFF_INST(type, name) `` | Flop reset to `'0` | `type name, n_name;` + flop |
    | `` `DFFR_INST(type, name, rval) `` | Flop with explicit reset value | `type name, n_name;` + flop |
    | `` `DFFNR_INST(type, name) `` | Flop with no reset | `type name, n_name;` + flop |
    | `` `DFFEN_INST(type, name, en) `` | Flop with enable | `type name, n_name;` + flop |
    | `` `DFFREN(q, d, en, rval) `` | Flop with reset+enable (raw) | flop only (no signal decl) |
    | `` `DFFR(q, d, rval) `` | Flop with reset (raw) | flop only (no signal decl) |
    | `` `DFF(q, d) `` | Flop reset to `'0` (raw) | flop only (no signal decl) |
    | `` `DFFEN(q, d, en) `` | Flop with enable (raw) | flop only (no signal decl) |
    | `` `DFFNR(q, d) `` | Flop with no reset (raw) | flop only (no signal decl) |
    | `` `SCFF(q, s, c) `` | Set-clear flop, set priority (raw) | flop only (no signal decl) |

    The `_INST` macros declare both the signal and its `n_<name>` next-state signal automatically. The raw macros require you to declare signals yourself -- use `nxt_<name>` as the convention for manually declared next-state signals.

    **FPGA vs ASIC Behavior:**
    *   **FPGA** (default): Uses `initial` for reset values, `always_ff` without reset.
    *   **ASIC** (`ASIC` define): Uses synchronous reset in `always_ff`.
    *   Write code the same way; the macros handle the difference.

    **Pattern: Declare then Drive:**

    ```systemverilog
    `DFF_INST(logic, stg1_valid)
    `DFF_INST(data_t, stg1_data)

    always_comb begin
        n_stg1_valid = in_port.vld;
        n_stg1_data = in_port.data;
    end
    ```

    **Pattern: Custom Reset Value:**

    ```systemverilog
    `DFFR_INST(count_t, counter, MAX_COUNT)

    always_comb begin
        n_counter = counter;
        if (decrement) n_counter = counter - 1'b1;
    end
    ```

5.  **Combinational Logic:**
    *   Always use `always_comb`.
    *   Assign default values at the top of the block to prevent latches.
    *   One `always_comb` per logical section (pipeline stage, functional unit).
    *   Use `begin`/`end` for all conditional blocks.

6.  **Combinational Intermediate Signals:**

    Not all signals need flops. Declare combinational intermediates at module scope and drive them in `always_comb`. These are zero-cost in hardware (just wires):

    ```systemverilog
    addr_t derived_addr;
    logic  is_aligned;

    always_comb begin
        derived_addr = base_addr + offset;
        is_aligned = (derived_addr[1:0] == 2'b00);
    end
    ```

    Use this for bit-slicing decomposition, derived flags, and any intermediate value consumed in the same or next cycle.

7.  **Assertions (`qAssert` / `qAssertFatal`):**
    *   `qAssert(condition, "message")` -- logs error but continues simulation.
    *   `qAssertFatal(condition, "message")` -- halts simulation immediately.

    ```systemverilog
    `qAssert(count <= MAX_COUNT, "Counter overflow detected")
    `qAssertFatal(state != ILLEGAL_STATE, "Illegal state reached")
    ```

8.  **Type Casting and Constants:**

    ```systemverilog
    addr_t'(bus_addr) & 32'h7f
    count_t'(MAX_VALUE)
    $signed({1'b0, unsigned_val})    // Zero-extend to signed

    localparam int unsigned DATA_WIDTH = 32'h0000_0008;
    localparam DERIVED_W = DATA_WIDTH + 2;
    typedef logic signed [DERIVED_W-1:0] accum_t;
    ```

9.  **Package Organization:**

    ```systemverilog
    package <block>_package;
    import shared_types_package::*;

    localparam int unsigned SOME_WIDTH = 32'h0000_0012;
    typedef logic [SOME_WIDTH-1:0] data_t;

    typedef struct packed {
        data_t value;
    } entry_t;

    endpackage : <block>_package
    ```

10. **Verilator Lint Pragmas:**

    ```systemverilog
    /* verilator lint_off WIDTHTRUNC */
    // ... code with intentional width truncation ...
    /* verilator lint_on WIDTHTRUNC */

    /* verilator lint_off WIDTHEXPAND */
    // ... code with intentional width expansion ...
    /* verilator lint_on WIDTHEXPAND */
    ```

11. **Key Idioms:**
    1.  Use `logic` everywhere, never `reg` or `wire`.
    2.  Use `'0` for zero, `'1` for all-ones.
    3.  Use `case () inside` for address decoding.
    4.  Use `32'hBADD_C0DE` as default read data for invalid APB addresses.
    5.  Use `automatic` keyword in functions and loop variables.
    6.  Use reduction `|` for overflow detection: `|accum[MSB:DATA_WIDTH]`.
    7.  Use ternary chains for mux-like selections.
    8.  Propagate `vld` and sideband metadata through every pipeline stage.
    9.  `assign in_port.rdy = 1'b1;` when module applies no backpressure.
