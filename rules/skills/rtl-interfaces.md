---
name: rtl-interfaces
description: Guide for using standard interface protocols (rdy_vld, push_ack, axi, status_if, external_reg_if, memory_if) in SystemVerilog RTL
---
# Skill: RTL Interfaces

## Purpose
Guide the user on using standard interface protocols (`rdy_vld`, `push_ack`, `axi`, `status_if`, `external_reg_if`, `memory_if`) in SystemVerilog.

## Implementation Location
All logic described below must be placed **after** the `// GENERATED_CODE_END` marker in your SystemVerilog file. **DO NOT** modify the auto-generated interface ports at the top of the file.

## Instructions

1.  **Port Directions (Modports):**

    | Modport | Meaning | Used for |
    |---------|---------|----------|
    | `.dst` | Destination (consumer) | Input streams, config inputs |
    | `.src` | Source (producer) | Output streams, status outputs |
    | `.master` | Bus master | AXI initiator |
    | `.slave` | Bus slave | AXI target |

2.  **Interface Types:**

    | Interface | Purpose | Key signals |
    |-----------|---------|-------------|
    | `rdy_vld_if` | Streaming data | `.vld`, `.rdy`, `.data` |
    | `push_ack_if` | Transactional request/response | `.push`, `.ack`, `.data` |
    | `req_ack_if` | Simple handshake (no data) | `.req`, `.ack` |
    | `status_if` | Config/status registers | `.data` |
    | `apb_if` | Register bus | `.psel`, `.penable`, `.pwrite`, `.paddr`, `.pwdata`, `.prdata`, `.pready`, `.pslverr` |
    | `memory_if` | Memory access | `.addr`, `.write_data`, `.read_data`, `.enable`, `.wr_en` |
    | `external_reg_if` | External register (write-pulse) | `.write`, `.wdata`, `.rdata` |
    | `axi_read_if` / `axi_write_if` | AXI4 bus | Standard AXI signals |

3.  **Usage (Ports):**
    *   Declare interfaces in module header.
    *   Use modports for direction.

    ```systemverilog
    module my_module (
        rdy_vld_if.dst data_in,  // Input stream
        rdy_vld_if.src data_out, // Output stream
        status_if.dst config,    // Config register input
        status_if.src status,    // Status register output
        axi_read_if.master axi_m // AXI Master port
    );
    ```

4.  **Ready/Valid (`rdy_vld_if`):**

    ```systemverilog
    always_comb begin
        data_in.rdy = 1'b0;
        data_out.vld = 1'b0;
        data_out.data = '0;

        if (data_in.vld) begin
            data_in.rdy = 1'b1;
            data_out.data = process(data_in.data);
            data_out.vld = 1'b1;
        end
    end
    ```

    For modules that are always ready (no backpressure):
    ```systemverilog
    assign data_in.rdy = 1'b1;
    ```

5.  **`status_if` (Config/Status Registers):**

    **Reading config (`.dst` direction):** `status_if.data` is always valid and can be read combinationally:
    ```systemverilog
    `DFF_INST(logic, mode_flag)
    always_comb begin
        n_mode_flag = (config.data.mode == ACTIVE) ? 1'b1 : 1'b0;
    end
    ```

    **Writing status back (`.src` direction):** Drive computed values for CPU readback:
    ```systemverilog
    always_comb begin
        status.data = computed_result;
    end
    ```

6.  **`external_reg_if` (Write-Pulse Commands):**

    Provides a single-cycle write pulse (`|write`) rather than a level. Use for command registers (e.g., clear, trigger):

    ```systemverilog
    `DFF_INST(logic, cmd_flag)
    always_comb begin
        n_cmd_flag = cmd_flag;
        if (|cmd_reg.write) begin
            n_cmd_flag = cmd_reg.wdata.trigger;
        end
        if (done_condition && cmd_flag) begin
            n_cmd_flag = 1'b0;
        end
    end
    ```

7.  **`memory_if` (Memory Access):**

    **Signals:**

    | Signal | `.src` direction | Purpose |
    |--------|-----------------|---------|
    | `addr` | output | Address (parameterized `addr_t`) |
    | `write_data` | output | Write data (parameterized `data_t`) |
    | `enable` | output | Port enable (must be high for read or write) |
    | `wr_en` | output | Write enable (0 = read, 1 = write) |
    | `read_data` | input | Read data (valid 1 cycle after `enable`) |

    **Read Timing:** `read_data` is registered inside `memory_dp` and valid **one cycle after** `enable` is asserted. Drive address in stage N, consume `read_data` in stage N+1.

    **Driving from a core module:**
    ```systemverilog
    always_comb begin
        mem.write_data = '0;
        mem.wr_en = 1'b0;
        mem.addr = '0;
        mem.enable = 1'b0;

        if (read_condition) begin
            mem.addr = target_addr;
            mem.enable = 1'b1;
        end
    end
    ```

    **Instantiation at container level** using `memory_dp`:
    ```systemverilog
    memory_if #(.data_t(mem_data_t), .addr_t(mem_addr_t)) mem_core();
    memory_if #(.data_t(mem_data_t), .addr_t(mem_addr_t)) mem_reg();

    memory_dp #(.DEPTH(MEM_DEPTH), .data_t(mem_data_t)) uMem (
        .mem_portA (mem_core),
        .mem_portB (mem_reg),
        .clk (clk)
    );
    ```

    **Conditional multi-port access:** Drive all ports with the same address but conditional `enable`:
    ```systemverilog
    mem_a.addr = target_addr;
    mem_a.enable = select_a;
    mem_b.addr = target_addr;
    mem_b.enable = ~select_a;
    data_val = select_a ? mem_a.read_data.val : mem_b.read_data.val;
    ```

    **FSM-sequenced reads:** When multiple addresses must be read sequentially, use an FSM. See `rtl-patterns.md` for the paired-FSM pattern.

8.  **Instantiating Internal Interfaces:**

    ```systemverilog
    status_if #(.data_t(config_t)) internal_config();
    rdy_vld_if #(.data_t(result_t)) processed_stream();
    memory_if #(.data_t(mem_data_t), .addr_t(mem_addr_t)) mem_rd [NUM_PORTS-1:0]();
    ```

9.  **AXI Usage:**
    *   Drive individual AXI signals (e.g., `axi_m.arvalid`, `axi_m.araddr`).
    *   Use `axi_pkg` structs for clean data handling (`axi_m.rdata.data`, `axi_m.bresp`).

    ```systemverilog
    axi_m.arvalid = start_read;
    axi_m.araddr = target_addr;
    if (axi_m.arready && axi_m.arvalid) begin
        // Read accepted
    end
    ```
