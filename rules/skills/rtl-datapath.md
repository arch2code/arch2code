---
name: rtl-datapath
description: Guide for using the A2C Pro datapath modules (rdyVldFifo, inPlaceList, rdyVldCapture, incDec) in SystemVerilog
---
# Skill: RTL datapath

## Purpose
Buffer, queue and count with the datapath modules.

## Availability
These modules ship only with A2C Pro, in `builder/pro/common/systemVerilog`. `a2cPro.f` adds that directory to the Verilator path. A base-only project does not have them and writes its own.

## Instructions

Instantiate the modules after `// GENERATED_CODE_END`. `.*` binds `clk` and `rst_n`, the block's default domain. A module on another clock binds that clock and its own reset explicitly, `.clk(clkSlow), .rst_n(rstSlow_n)` (`rtl-core.md`).

### 1. FIFO (`rdyVldFifo`)
*   Parameters: `dataSt`, `DEPTH` (default 16).
*   Ports: `write` (`rdy_vld_if.dst`), `read` (`rdy_vld_if.src`), `clk`, `rst_n`.
*   `write.rdy` is low only when the FIFO is full. `read.vld` is high whenever it holds an entry, and `read.data` shows the oldest entry in the same cycle.
*   A write and a read can complete in the same cycle. A write to a full FIFO waits even if a read completes that cycle.
*   Entries are flops, not a RAM, so size `DEPTH` with that cost in mind.
*   It has one clock. Neither base nor Pro has an asynchronous FIFO.

```systemverilog
rdy_vld_if #(.data_t(cmdSt)) cmdQ();

rdyVldFifo #(.dataSt(cmdSt), .DEPTH(8)) uCmdFifo (
    .write (cmdIn),
    .read  (cmdQ),
    .*
);
```

`cmdIn` is a `rdy_vld_if.dst` port of the block. `cmdQ` is a local interface instance your logic drains.

### 2. Capture register (`rdyVldCapture`)
Takes one item from a `rdy_vld_if` and holds it until you release it.
*   Ports: `captureIf` (`rdy_vld_if.dst`), `capData`, `dataVld`, `clear`.
*   `captureIf.rdy` is high while it holds nothing. It captures `data` on the first valid cycle and raises `dataVld` the next cycle.
*   Pulse `clear` to release the held item. It can capture again the cycle after, so it takes at most one item every two cycles.
*   Use it to hold one command for a multi-cycle operation, not to stream.

```systemverilog
rdyVldCapture #(.dataSt(cmdSt)) uCmdCapture (
    .captureIf (cmdIn),
    .capData   (cmd),
    .dataVld   (cmdVld),
    .clear     (cmdDone),
    .*
);
```

### 3. Up/down counter (`incDec`)
*   Parameters: `dataSt`.
*   Ports: `inc`, `dec`, `count`.
*   `inc` adds one and `dec` subtracts one. Both together, or neither, hold the count.
*   It wraps. It has no overflow or underflow protection.

Guard at the source. Stop the requester at the limit and count what actually happens. Here `issueOk` both starts the command and drives `inc`:

```systemverilog
assign issueOk = issueReq && (inFlight != MAX_IN_FLIGHT);

incDec #(.dataSt(cmdCountT)) uInFlight (
    .inc   (issueOk),
    .dec   (retire),
    .count (inFlight),
    .*
);
```

### 4. Linked lists in a memory (`inPlaceList`)
Keeps `NUM_LIST` FIFO-ordered linked lists of items whose IDs index a memory, such as free tag lists. Each item is stored at its own ID in the memory, and the memory row also holds the link to the next item.
*   It needs `rrArb` and `fsmDefs.svh`, both in Pro.
*   Parameters: `dataSt`, `nextSt`, `NUM_LIST`. There is no item-count parameter. The memory's depth sets the number of items.
*   `dataSt` must be a struct with a field named `next` of type `nextSt`. On push, `next` holds the item's own ID, which is the memory address the item is written to. On pop, `next` again holds the item's ID.
*   Ports per list `i`: `pushData[i]`, `pushDataVld[i]`, `pushDataAck[i]`, `popData[i]`, `popDataVld[i]`, `popDataAck[i]`, `count[i]`.
*   Out of reset every list is empty. The module does not fill a free list, so push each free ID once after reset.
*   `count[i]` counts the items in memory and excludes the one waiting in `popData[i]`.
*   Push: hold `pushDataVld[i]` and `pushData[i]` until `pushDataAck[i]`.
*   Pop: `popDataVld[i]` is high while list `i` has an item ready in `popData[i]`. Pulse `popDataAck[i]` to take it.
*   `dataTable` is a `memory_if.src` to a memory of `dataSt` rows with one-cycle read latency, as the generated memories have (`rtl-interfaces.md`).
*   One FSM serves every list, so one push or refill runs at a time. A push into a non-empty list takes four cycles.

```systemverilog
inPlaceList #(
    .dataSt   (tagEntrySt),
    .nextSt   (tagIdT),
    .NUM_LIST (1)
) uFreeTags (
    .pushData    (freeTagPushData),
    .pushDataVld (freeTagPushVld),
    .pushDataAck (freeTagPushAck),
    .popData     (freeTagPopData),
    .popDataVld  (freeTagPopVld),
    .popDataAck  (freeTagPopAck),
    .count       (),
    .dataTable   (tagTable),
    .*
);
```
