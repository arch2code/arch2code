---
name: rtl-registers
description: Guide for implementing register logic in SystemVerilog including decoder architecture and external register handling
---
# Skill: RTL Registers

## Purpose
Guide the user in implementing the **RTL-side logic for external (`ext`)
registers** and driving `ro`/`rw` register ports. The decoder and the register
handlers are generated — this skill covers only the user RTL you write inside a
block to back its registers.

## References
*   **Decode hierarchy (router/leaf model):** `design-register-decode.md`
*   **Main Rules:** `ARCH2CODE_AI_RULES.md` (See "Register Decoder Architecture")

## Prerequisites
*   Registers and memories must already be defined in the YAML architecture (see `design-architecture.md`).
*   The block must be a routed leaf served by a generated `addressBlock:` router (see `design-register-decode.md`). You do **not** write the decoder.

## Instructions

1.  **Register Decoder Architecture (RTL View) — all generated:**
    *   **Router (generated):** the `addressBlock:` block's RTL comes from the `apbDecodeModule` template (scaffolded by `make newmodule`). It routes the register bus to served instances. You never write it.
    *   **Block-level handler (generated):** each routed leaf block (e.g., `dma_controller`) gets an auto-generated `<block>_regs` instance that decodes registers/memories defined in YAML. You never write it.
    *   **Your RTL** only provides the storage/side-effects for `ext` registers and drives `ro` read data, as below.

    > For reusable-IP leaves that ship their own register-bus port, the IP block authors one `registerPorts:` row (e.g. `registerPorts: { regs: { interface: ipReg } }`) so its generated `<block>Base` stays self-contained. Plain top-down leaves omit it. See `design-register-decode.md`.

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
