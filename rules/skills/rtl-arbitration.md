# Skill: RTL Arbitration

## Purpose
Guide the user on using arbitration modules (`memArb`, `vldAckArb`) in SystemVerilog to manage shared resources.

## Implementation Location
All module instantiations and logic described below must be placed **after** the `// GENERATED_CODE_END` marker in your SystemVerilog file. **DO NOT** modify the auto-generated ports or parameters at the top of the file.

## Instructions

1.  **Memory Arbitration (`memArb`):**
    *   **Use Case:** Multiple requestors accessing a single memory port.
    *   **Parameters:** `NUM_ARB_RD` (read ports), `NUM_ARB_WR` (write ports).
    *   **Ports:** Concatenate request, address, data arrays.

    ```systemverilog
    // Example from tagScheduler.sv
    memArb
    #(
        .dataSt         (cmdIdSt),
        .addrSt         (hostRdTagT),
        .NUM_ARB_RD     (1),
        .NUM_ARB_WR     (1)
    )
    uRdTagTableArb(
        .rdReq    (rdTagTableRdReq),
        .rdLock   (1'b0),
        .rdAddr   (rdTagTableRdAddr),
        .rdData   (rdTagTableRdData),
        .rdAck    (rdTagTableRdAck),
        .wrReq    (rdTagTableWrReq),
        .wrAddr   (rdTagTableWrAddr),
        .wrData   (rdTagTableWrData),
        .wrAck    (rdTagTableWrAck),
        .memoryIf (rdTagTable), // Physical memory port
        .*
    );
    ```

2.  **Interface Arbitration (`vldAckArb`):**
    *   **Use Case:** Multiple sources writing to a single destination interface (valid/ack protocol).
    *   **Parameters:** `NUM_ARB`.
    *   **Ports:** Concatenate `arbVld`, `arbAck`, `arbData`.

    ```systemverilog
    // Example from mPageMap.sv
    vldAckArb
    #(
        .dataSt  (mPageLockSt),
        .NUM_ARB (2)
    )
    uMPageUnlockVldAckArb(
        .arbVld  ({mPageUnlockSTULDataVld, mPageUnlockMLULDataVld}),
        .arbAck  ({mPageUnlockSTULDataAck, mPageUnlockMLULDataAck}),
        .arbData ({mPageUnlockSTULData, mPageUnlockMLULData}),
        .vld     (mPageUnlock.push), // Final destination valid
        .ack     (mPageUnlock.ack),  // Final destination ack
        .data    (mPageUnlock.data), // Final destination data
        .*
    );
    ```

3.  **Lock Location (`lockLocation`):**
    *   **Use Case:** Requesting locks on resources (often used with `mapHashLock` logic).
    *   **Ports:** `req`, `lockReq`, `location`, `gnt`.

    ```systemverilog
    lockLocation 
    #(
      .NUM_REQ (4),
      .lockT   (mpMapCacheLockT)
    )
    uMapHashLock(
      .req      ({req1, req2, req3, req4}),
      .lockReq  ({lock1, lock2, lock3, lock4}),
      .location ({loc1, loc2, loc3, loc4}),
      .gnt      ({gnt1, gnt2, gnt3, gnt4}),
      .*
    );
    ```
