---
name: systemc-synchronization
description: Guide for using synchLock, events, and arbitration patterns in SystemC for concurrency and shared resources
---
# Skill: SystemC Synchronization

## Purpose
Guide the user on using `synchLock`, events, and arbitration patterns in SystemC to model concurrency and shared resources correctly.

## Implementation Location
All logic and member usage described below must be implemented in the user regions of the block's `model/<block>.cppm` module file, specifically **after** the `// GENERATED_CODE_END` markers.

## Instructions

1.  **Multi-Interface Arbitration Pattern:**
    *   **Use Case:** When a thread needs to service multiple input interfaces.
    *   **Family support:** `setExternalEvent`/`isActive`/`isNotActive` is available on every base channel family's receive side: `rdy_vld`, `apb`, `memory`, `req_ack`, `push_ack`, `pop_ack`, `notify_ack`. On `axi_read` and `axi_write`, the trio is on the **dst modport** and reflects the address sub-channel (the arbitration decision an interconnect or multi-port subordinate makes); a single `SC_THREAD` can service N `axi_read`/`axi_write` dst ports via one shared event this way. `axi4_stream` forwards to its one data channel. `external_reg`, `raw`, and `status` only carry `setExternalEvent` (no `isActive`/`isNotActive`), predate this pattern, and do not support the scan-then-wait idiom below.
    *   **Mechanism:**
        1.  Create a shared `sc_event`.
        2.  Bind interfaces to this event using `setExternalEvent(&event)`.
        3.  Wait on the event in a loop.
        4.  Check `isActive()` on interfaces to see which one woke the thread.
        5.  Arbitrate if multiple are active.

    ```cpp
    // 1. Setup (Constructor/Init)
    sc_event commonEvent;
    cmdFetchReq->setExternalEvent(&commonEvent);
    dataResp->setExternalEvent(&commonEvent);

    // 2. Loop
    while(true) {
        // Wait until at least one interface is active
        while (cmdFetchReq->isNotActive() && dataResp->isNotActive()) {
            wait(commonEvent);
        }

        // 3. Check & Arbitrate
        if (cmdFetchReq->isActive()) {
            dmaReadRequestSt request;
            cmdFetchReq->pushReceive(request);
            // ... process ...
            cmdFetchReq->ack();
        } else if (dataResp->isActive()) {
            // ... process ...
        }
    }
    ```

2.  **Arbitration with `synchLock`:**
    *   **Do NOT** use simple `if/else` on ports for cycle-accurate modeling. Use `synchLockFactory` to create an arbiter that mimics RTL behavior.
    *   **Pattern:**
        1.  Determine purely local winner (priority encoder).
        2.  Call `arbiter->arb(winner)` to handle cycle-accurate delays and fairness.
        3.  Switch on result.
        4.  Execute transaction.

    ```cpp
    // Example of arbitration pattern
    _axiIdT arbResult = 0;

    // 1. Determine local winner
    if (cmdFetchReq->isActive()) {
        arbResult = AXIRD_CMDFETCH_ID;
    } else if (descFetchReq->isActive()) {
        arbResult = AXIRD_PTRFETCH_ID;
    } // ...

    // 2. Synchronize with RTL/SystemC arbiter
    arbResult = readAddressArbiter->arb(arbResult);

    // 3. Process winner
    switch (arbResult) {
        case AXIRD_CMDFETCH_ID:
            cmdFetchReq->pushReceive(request);
            // ...
            break;
        // ...
    }
    ```

3.  **Locks/Mutexes:**
    *   Use `synchLock` for mutual exclusion, especially when accessing shared data structures across threads.
    *   Initialize using `synchLockFactory::getInstance().newLock(...)`.
    *   Use `lock(state)` and `unlock(state)` or `RAII` pattern if available.
    *   `state` parameter is useful for debugging/waveforms to indicate *why* the lock is held.

    ```cpp
    // Initialization
    std::shared_ptr<synchLock<>> writeAccountingMutex;
    writeAccountingMutex(synchLockFactory<>::getInstance().newLock(getAltName(), "writeAccountingMutex"));

    // Usage
    writeAccountingMutex->lock(TAGSCHEDULER_WRITEACC_SCHEDULE);
    writesInTransfer++;
    writeAccountingMutex->unlock();
    ```
