---
name: rtl-registers
description: Guide for the hand-written RTL behind a block's registers - driving ro registers, reading rw registers, implementing ext registers, the register clock domain, and wide-register access
---
# Skill: RTL registers

## Purpose
Write the RTL a routed leaf needs behind its registers. The generator writes the decoder and each block's register handler. You write only the logic that drives `ro` values, reads `rw` values and backs `ext` registers.

## References
*   `design-register-decode.md` owns the decode hierarchy: routers, routed leaves, `registerPorts:`, register clocks, memories on another clock, and what an unclaimed address reads (`32'hBADD_C0DE`).
*   `rtl-core.md` owns the flop macros and clock domains.

## Prerequisites
*   The registers and memories are defined in YAML (`design-architecture.md`).
*   A generated `addressBlock:` router serves the block (`design-register-decode.md`).

## Instructions

### 1. What is generated
*   **Router.** The `addressBlock:` block's RTL comes from the `apbDecodeModule` template. The module is named after the router block.
*   **Register handler.** Each routed leaf gets a handler instance in its generated region. The handler module is named `<block>` plus the suffix in `project.yaml` `fileGeneration: regBlockNaming: blockSuffix`. The default is `_regs`, and the examples set `Regs` (`blockARegs`). Every access completes without PSLVERR.
*   **Register ports.** The generated region declares one interface instance per register and binds it to the handler. Your RTL uses these instances by register name.

| `regType` | Interface instance | Your RTL |
| :--- | :--- | :--- |
| `ro` | `status_if` | drives `<reg>.data` |
| `rw` | `status_if` | reads `<reg>.data` |
| `ext` | `external_reg_if` | reads `<reg>.write` and `<reg>.wdata`, drives `<reg>.rdata` |

`external_reg_if` has no read strobe, so reading an `ext` register cannot trigger logic such as clear-on-read.

### 2. Register clock domain
The handler runs on the block's register clock and reset. For a top-down leaf, these are the leaf's synchronous input reset bound to the serving router's bus reset, and the clock that owns that reset. A `registerPorts:` row can name them instead. `design-register-decode.md` covers both.

*   Write flops that capture `<reg>.write` and `<reg>.wdata` on the register clock. If the register clock and reset are the block's `clk` and `rst_n`, use the bare macros. Otherwise use the `_DOM` form, for example `` `DFFR_INST_DOM(<regClock>, <regReset>, <type>, <name>, <rval>) ``.
*   The handler samples `ro` and `ext` read data on the register clock without synchronising it. If your logic for that data runs on another clock, the read crosses clock domains.

### 3. `ro` registers
Drive the whole structure or its fields:

```systemverilog
assign roA.data.busy     = busy;
assign roA.data.errorCnt = errorCnt;
```

### 4. `rw` registers
The handler holds the value. Read it as `<reg>.data` or `<reg>.data.<field>`:

```systemverilog
assign enable = ctrlReg.data.enable;
```

### 5. `ext` registers
The handler gives no storage. `<reg>.write` is nonzero for one cycle per firmware write, with `<reg>.wdata` holding the value. Drive `<reg>.rdata` with the value firmware reads back.

```systemverilog
localparam un0ExtRegSt EXTA_RESET = '{fa: 8'h61, fb: 16'h1234, fc: 8'h63};
`DFFR_INST(un0ExtRegSt, extAReg, EXTA_RESET)
always_comb begin
    n_extAReg = extAReg;
    if (|extA.write) begin
        n_extAReg = extA.wdata;
    end
end

assign extA.rdata = extAReg;
```

`un0ExtRegSt` is the register's YAML `structure:`. The generator writes it into the context package under the same name and declares `extA` as `external_reg_if #(.data_t(un0ExtRegSt))`. The reset value is yours to write, as `EXTA_RESET` is here. The handler applies `defaultValue:` to `rw` registers only.

Put side effects of the write, such as starting a command, in the same `if (|extA.write)` branch.

### 6. Unused memory ports
A block-side memory port your RTL does not use, such as the read port of a table only firmware touches, still needs driving. Tie it off after the generated region:

```systemverilog
assign tbl.enable     = 1'b0;
assign tbl.wr_en      = 1'b0;
assign tbl.addr       = '0;
assign tbl.write_data = '0;
```

### 7. Registers wider than 32 bits
*   The register bus is 32 bits wide, so a wider register spans consecutive words: bits `[31:0]` at offset `+0`, bits `[63:32]` at `+4`, and so on.
*   Each word write to an `rw` register takes effect on its own. After a write to `+0` the register holds the new low word next to the old high word.
*   A memory row behaves differently. The handler stages the lower words and writes the whole row to the memory when firmware writes the row's highest word.
*   An `ext` register is at most the bus width, and `make db` rejects a wider one. Firmware writes it in one access, so its owner sees one `write` carrying the whole value. Split wider external state into several `ext` registers.
*   An `rw` or `ro` register with a parameterizable structure spans the words of its widest variant in every variant. Words above the bound variant's width read 0 and drop writes.
*   Firmware that needs a consistent `rw` value writes the word that completes it last, usually the highest. To read a value that hardware changes, read the high word, the low word, then the high word again, and retry if the two high reads differ.
