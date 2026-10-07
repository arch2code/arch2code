---
name: rtl-interfaces
description: Guide for using standard interface protocols (rdy_vld, push_ack, req_ack, pop_ack, notify_ack, status, external_reg, memory, apb, axi, axi4_stream, raw) in SystemVerilog RTL
---
# Skill: RTL interfaces

## Purpose
Drive and read the standard arch2code interfaces in hand-written SystemVerilog.

## Ports come from YAML
The generator declares every interface port, interface instance and memory instance from the YAML, inside the generated region. Do not declare them by hand. To add or change a port, edit the YAML connection and regenerate (`design-architecture.md`). Your logic goes after `// GENERATED_CODE_END`.

## Instructions

### 1. Modports
Every interface has two modports and no others:

| Modport | Side | Example |
| :--- | :--- | :--- |
| `.src` | Producer, initiator | stream output, AXI initiator, `ro` value driver |
| `.dst` | Consumer, target | stream input, AXI target, `status` input |

### 2. Interface types

| Interface | Purpose | Signals |
| :--- | :--- | :--- |
| `rdy_vld_if` | Stream, non-blocking | `vld`, `data` from src; `rdy` from dst |
| `push_ack_if` | Push a transaction | `push`, `data` from src; `ack` from dst |
| `req_ack_if` | Request with response data | `req`, `data` from src; `ack`, `rdata` from dst |
| `pop_ack_if` | Pull data from dst | `pop` from src; `ack`, `rdata` from dst |
| `notify_ack_if` | Event with no data | `notify` from src; `ack` from dst |
| `status_if` | Level value such as config or status | `data` |
| `external_reg_if` | Register owned outside the handler | `write`, `wdata` from src; `rdata` from dst |
| `memory_if` | Memory port | `addr`, `write_data`, `enable`, `wr_en` from src; `read_data` from dst |
| `apb_if` | Register bus | `psel`, `penable`, `pwrite`, `paddr`, `pwdata` from src; `pready`, `prdata`, `pslverr` from dst |
| `axi_read_if`, `axi_write_if` | AXI4 | standard AXI4 channel signals |
| `axi4_stream_if` | AXI4-Stream | `tvalid`, `tdata`, `tstrb`, `tkeep`, `tlast`, `tid`, `tdest`, `tuser`; `tready` from dst |
| `raw_if` | Last resort, no handshake | `data` |

The SV definitions are in `builder/base/interfaces/<name>/<name>_if.sv`.

### 3. `rdy_vld_if`
A transfer happens in a cycle where `vld && rdy`. The source holds `vld` and `data` until then. A pass-through stage passes backpressure upstream:

```systemverilog
always_comb begin
    dataOut.vld  = dataIn.vld;
    dataOut.data = process(dataIn.data);
    dataIn.rdy   = dataOut.rdy;
end
```

Tie `dataIn.rdy = 1'b1` only when the block can accept every cycle.

### 4. `notify_ack_if`
The source raises `notify` and holds it until a cycle where `notify && ack`. The destination raises `ack` for one cycle per event, in the first `notify` cycle or any later one. `notify` still high in the cycle after that handshake is a new event.

### 5. `status_if`
`data` is a level, always valid. Read it combinationally on the `.dst` side and drive it on the `.src` side:

```systemverilog
`DFF_INST(logic, modeFlag)
always_comb begin
    n_modeFlag = (cfg.data.mode == ACTIVE);
end

assign status.data = computedResult;
```

`config` is a SystemVerilog keyword, so never name a port `config`.

### 6. `external_reg_if`
`write` is nonzero for one cycle per firmware write, with the value on `wdata`. The owner drives `rdata`. `write` is a 2-bit vector. Test it with `|write`. `rtl-registers.md` has the full owner pattern.

```systemverilog
`DFF_INST(logic, cmdFlag)
always_comb begin
    n_cmdFlag = cmdFlag;
    if (|cmdReg.write) begin
        n_cmdFlag = cmdReg.wdata.trigger;
    end
    if (doneCondition && cmdFlag) begin
        n_cmdFlag = 1'b0;
    end
end
```

### 7. `memory_if`
*   `enable` must be high for a read or a write. `wr_en` selects write (1) or read (0).
*   `read_data` is registered inside the memory, so it is valid the cycle after the read's `enable`. Drive the address in cycle N and use `read_data` in cycle N+1.
*   Drive every `.src` signal on every cycle. Give each a default at the top of the `always_comb`.

```systemverilog
always_comb begin
    mem.write_data = '0;
    mem.wr_en      = 1'b0;
    mem.addr       = '0;
    mem.enable     = 1'b0;
    if (readCondition) begin
        mem.addr   = targetAddr;
        mem.enable = 1'b1;
    end
end
```

The generator instantiates each memory the block declares, inside the generated region. It picks `memory_sp` or `memory_dp` from the port count. It adds `_2clk` when the two ports run on different clocks, and `_ext` for a `local: true` memory. Never hand-write a memory instance or its `memory_if` instances. To get a different memory, change the memory's `memoryType`, `regAccess`, `clock:` or `local:` in YAML.

A block that owns a memory drives the block-side `memory_if` instance the generated region declares, which is named after the memory. A child block that `memoryConnections` connects to its container's memory gets a `memory_if.src` port, and drives it the same way.

To read several addresses in sequence, see `rtl-patterns.md` (FSM-sequenced memory reads).

### 8. `raw_if`
Use `raw_if` only at a design boundary, to match external IP with a free-running data bus and no handshake. Prefer `rdy_vld_if` or another handshaked interface everywhere else.
*   Sample `data` on the clock. Do not add backpressure to this interface.
*   Convert to `rdy_vld_if` at the first internal stage.

```systemverilog
`DFF_INST(videoSt, sampledData)
assign n_sampledData = csiVideoIn.data;
```

### 9. AXI
Drive the channel signals directly. `rdata` is the interface's `data_t`, and `bresp` is on `axi_write_if` only.

```systemverilog
assign axiRd.arvalid = startRead;
assign axiRd.araddr  = targetAddr;
// address accepted in a cycle where axiRd.arvalid && axiRd.arready
```
