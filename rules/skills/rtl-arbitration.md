---
name: rtl-arbitration
description: Guide for using the A2C Pro arbitration modules (memArb, vldAckArb, lockLocation, rrArb) in SystemVerilog
---
# Skill: RTL arbitration

## Purpose
Share one memory port or one destination between several requesters with the arbitration modules.

## Availability
These modules ship only with A2C Pro, in `builder/pro/common/systemVerilog`. `a2cPro.f` adds that directory to the Verilator path. A base-only project does not have them and writes its own arbiter.

## Instructions

Instantiate the modules after `// GENERATED_CODE_END`. Pack each request vector and array with a concatenation. The rightmost element is index 0.

### Clock and reset
`.*` binds `clk` and `rst_n`, which is the block's default domain (`rtl-core.md`). An arbiter on another clock binds that clock and its own reset explicitly: `.clk(clkSlow), .rst_n(rstSlow_n)`.

### 1. `rrArb`
Round-robin arbiter, used inside the others.
*   Parameters: `NUM_ARB`.
*   `gnt` is a one-hot grant of `req`, combinational. `gntIdx` is its index and `gntVld` is `|req`.
*   Pulse `next` when the granted requester is served. If `gnt` has been stable for a cycle, priority moves past that requester. If `next` comes in the grant's first cycle, the pointer advances one position from where it was, so the order is only approximately round-robin.

### 2. `memArb`
Several readers and writers share one `memory_if` port.
*   Parameters: `dataSt`, `addrSt`, `NUM_ARB_RD`, `NUM_ARB_WR`, `WRITE_PRIORITY` (default 1).
*   Each requester holds `rdReq[i]` and `rdAddr[i]`, or `wrReq[i]`, `wrAddr[i]` and `wrData[i]`, until its ack.
*   `rdAck` and `wrAck` are combinational, one-hot, and high in the cycle the memory is accessed.
*   `rdData` is one shared bus, not one per reader. It is valid the cycle after `rdAck`, for the reader that was acked.
*   With `WRITE_PRIORITY = 1` any write request beats every read, so continuous writes starve reads. With `0` writes go only when no read is requested.
*   `rdLock[i]` makes a read also take a lock on its address through `lockLocation`. The read is acked only when the lock is granted. The lock holds while `rdLock[i]` stays high and releases when it drops. Tie `rdLock` to `'0` when no reader locks.
*   A lock blocks only other locking reads (`rdLock` high) of the same address. Writes and non-locking reads ignore it. To make a read-modify-write atomic, every writer of the address must first take the lock through a locking read.

```systemverilog
memArb #(
    .dataSt     (tagEntrySt),
    .addrSt     (tagAddrT),
    .NUM_ARB_RD (2),
    .NUM_ARB_WR (1)
) uTagTableArb (
    .rdReq    ({rdReqB, rdReqA}),
    .rdLock   ('0),
    .rdAddr   ({rdAddrB, rdAddrA}),
    .rdData   (tagRdData),
    .rdAck    ({rdAckB, rdAckA}),
    .wrReq    (wrReq),
    .wrAddr   (wrAddr),
    .wrData   (wrData),
    .wrAck    (wrAck),
    .memoryIf (tagTable),
    .*
);
```

`tagTable` is the block-side `memory_if` of a memory the block declares in YAML (`rtl-interfaces.md`).

### 3. `vldAckArb`
Several sources share one valid/ack destination, such as a `push_ack_if`.
*   Parameters: `dataSt`, `NUM_ARB`.
*   Each source holds `arbVld[i]` and `arbData[i]` until `arbAck[i]`.
*   `vld` is high while any source is valid, and `data` is the granted source's data. `arbAck[i]` is high in the cycle the destination's `ack` meets `vld` for source `i`.

```systemverilog
vldAckArb #(
    .dataSt  (unlockSt),
    .NUM_ARB (2)
) uUnlockArb (
    .arbVld  ({unlockVldB, unlockVldA}),
    .arbAck  ({unlockAckB, unlockAckA}),
    .arbData ({unlockDataB, unlockDataA}),
    .vld     (unlock.push),
    .ack     (unlock.ack),
    .data    (unlock.data),
    .*
);
```

### 4. `lockLocation`
Grants a lock on a location, such as an address, to at most one holder at a time.
*   Parameters: `NUM_REQ`, `lockT`.
*   Raise `req[i]` with `location[i]`. `gnt[i]` rises in the same cycle if no current holder has that location.
*   Keep `lockReq[i]` high to hold the lock. `gnt[i]` stays high while it does. Drop `lockReq[i]` to release.
*   The check compares against locks held from earlier cycles, so two new requests for the same location in one cycle can both be granted. Present at most one new request per cycle, for example by driving `req` from a one-hot `rrArb` grant as `memArb` does.

```systemverilog
lockLocation #(
    .NUM_REQ (2),
    .lockT   (lockAddrT)
) uAddrLock (
    .req      ({reqB, reqA}),
    .lockReq  ({holdB, holdA}),
    .location ({locB, locA}),
    .gnt      ({gntB, gntA}),
    .*
);
```
