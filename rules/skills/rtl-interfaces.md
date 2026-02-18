# Skill: RTL Interfaces

## Purpose
Guide the user on using standard interface protocols (`rdy_vld`, `push_ack`, `axi`) in SystemVerilog.

## Implementation Location
All logic described below must be placed **after** the `// GENERATED_CODE_END` marker in your SystemVerilog file. **DO NOT** modify the auto-generated interface ports at the top of the file.

## Instructions

1.  **Interface Types:**
    *   **`rdy_vld` (Ready/Valid):** Standard streaming.
        *   **Source:** `valid` output, `data` output, `ready` input.
        *   **Destination:** `valid` input, `data` input, `ready` output.
    *   **`push_ack` (Push/Ack):** Transactional request/response.
        *   **Source:** `push` output, `data` output, `ack` input.
        *   **Destination:** `push` input, `data` input, `ack` output.
    *   **`req_ack` (Request/Acknowledge):** Simple handshake without data.
        *   **Source:** `req` output, `ack` input.
        *   **Destination:** `req` input, `ack` output.
    *   **AXI4 (`axi_read`, `axi_write`):** Standard bus interfaces.
        *   **Master:** `arvalid`, `araddr`, `rready`...
        *   **Slave:** `arready`, `rvalid`, `rdata`...

2.  **Usage (Ports):**
    *   Declare interfaces in module header.
    *   Use modports for direction (`src`, `dst`, `master`, `slave`).

    ```systemverilog
    module my_module (
        rdy_vld_if.dst data_in,  // Input stream
        rdy_vld_if.src data_out, // Output stream
        axi_read_if.master axi_m // AXI Master port
    );
    ```

3.  **Assignments:**
    *   **Data Assignment:** Always assign specific fields of the interface data struct, or the whole struct if types match.
    *   **Control Signals:** Drive valid/ready signals explicitly in logic.

    ```systemverilog
    always_comb begin
        // Default assignments (prevent latches)
        data_in.ready = 1'b0;
        data_out.valid = 1'b0;
        data_out.data = '0;

        if (data_in.valid) begin
            data_in.ready = 1'b1; // Accept input
            data_out.data = process(data_in.data);
            data_out.valid = 1'b1; // Drive output
        end
    end
    ```

4.  **AXI Usage:**
    *   Drive individual AXI signals (e.g., `axi_m.arvalid`, `axi_m.araddr`).
    *   Use `axi_pkg` structs for clean data handling (`axi_m.rdata.data`, `axi_m.bresp`).

    ```systemverilog
    // AXI Read Request
    axi_m.arvalid = start_read;
    axi_m.araddr = target_addr;
    if (axi_m.arready && axi_m.arvalid) begin
        // Read accepted
    end
    ```
