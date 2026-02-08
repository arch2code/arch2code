# Skill: SystemC Synchronization

## Purpose
Guide the user on using `synchLock`, events, and arbitration patterns in SystemC to model concurrency and shared resources correctly.

## Implementation Location
All logic and member usage described below must be implemented in the manual sections of your `.h` and `.cpp` files, specifically **after** the `// GENERATED_CODE_END` markers.

## Instructions

1.  **Multi-Interface Arbitration Pattern:**
    *   **Use Case:** When a thread needs to service multiple input interfaces.
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
