# Skill: RTL Core

## Purpose
Guide the user in writing core RTL modules in SystemVerilog, focusing on module structure, FSMs, and reset logic.

## Instructions

1.  **Module Structure & Generated Code:**
    *   **Auto-Generation:** The module declaration, interface ports, and package imports are **auto-generated** by `arch2code` based on the YAML definition.
    *   **Safe Zones:** **NEVER** modify code between `// GENERATED_CODE_BEGIN` and `// GENERATED_CODE_END` markers.
    *   **Implementation:** Place all manual logic (FSMs, internal signals, sub-module instances) after the generated sections.

    ```systemverilog
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

    endmodule
    ```

2.  **Finite State Machines (FSMs):**
    *   **Use Macros:** Do NOT write raw `case` statements for state machines. Use `fsmDefs.svh` macros.
    *   **Pattern:** `always_comb` block with `nState = state;` default.
    *   **States:** Define `enum logic [WIDTH-1:0] {STATE1, STATE2} statesT;`.

    ```systemverilog
    typedef enum logic [1:0] {RDY, WORK, DONE} statesT;
    `include "fsmDefs.svh" // Declares state, nState registers

    always_comb begin
        nState = state;
        // Default assignments
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

3.  **Flip-Flops:**
    *   Use `DFF` macro for standard registers: `` `DFF(q, d) ``.
    *   Use `DFFR` macro for registers with reset value: `` `DFFR(q, d, RESET_VAL) ``.
    *   **Do not** write explicit `always_ff @(posedge clk)` blocks unless absolutely necessary (e.g., complex reset logic not covered by macros).

4.  **Combinational Logic:**
    *   Always use `always_comb`.
    *   Assign default values at the top of the block to prevent latches.
