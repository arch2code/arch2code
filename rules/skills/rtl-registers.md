# Skill: RTL Registers

## Purpose
Guide the user in implementing register logic in SystemVerilog, focusing on the two-level decoder architecture and manual logic for external registers.

## References
*   **Main Rules:** `ARCH2CODE_AI_RULES.md` (See "Registers & Address Management" for decoder architecture details)

## Prerequisites
*   Registers and memories must already be defined in the YAML architecture (see `design-architecture.md`).
*   The top-level manual decoder (`apb_decode_system` etc.) must be instantiated in YAML.

## Instructions

1.  **Register Decoder Architecture (RTL View):**
    *   **Level 1 (Manual):** You implement the top-level decoder (e.g., `apb_decode_system`). This module receives the main bus and routes it to sub-blocks based on address ranges.
    *   **Level 2 (Automatic):** The generated block (e.g., `dma_controller`) contains an auto-generated instance (e.g., `dma_controller_regs`). This handles the internal decoding for registers defined in YAML.

2.  **Implementing External Registers (`regType: ext`):**
    *   **Concept:** For `ext` registers, the auto-generated block provides ports but NO internal storage or logic. You must implement this in your RTL.
    *   **Ports Provided:** 
        *   `<regName>_wr`: Write strobe (1 cycle).
        *   `<regName>_wdata`: Write data payload.
        *   `<regName>_rd`: Read strobe.
        *   `<regName>_rdata`: Read data input (you drive this).
    *   **Implementation Pattern:**
        ```systemverilog
        // In your module's IMPLEMENTATION section
        logic [31:0] my_ext_reg;

        always_ff @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
                my_ext_reg <= '0;
            end else if (my_ext_reg_wr) begin
                my_ext_reg <= my_ext_reg_wdata;
                // Add side effects here (e.g., start a transaction)
            end
        end

        // Drive read data
        always_comb begin
            my_ext_reg_rdata = my_ext_reg;
        end
        ```

3.  **Read-Only Registers (`regType: ro`):**
    *   **Concept:** Auto-generated logic handles the read bus protocol. You only need to provide the current value.
    *   **Ports Provided:** `<regName>_rdata` (input to generated block).
    *   **Implementation:**
        ```systemverilog
        // Drive status signals to the register port
        assign status_reg_rdata.busy = is_busy;
        assign status_reg_rdata.error_cnt = error_counter;
        ```

4.  **Read-Write Registers (`regType: rw`):**
    *   **Concept:** Fully handled by auto-generated code.
    *   **Usage:** Use the generated signals (typically `regs.regName.field`) if you need to read the value in your logic.
    *   **Note:** Check generated signal names in the header of the generated `.sv` file.
