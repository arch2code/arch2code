---
name: systemc-synchronization
description: Guide for using shared events, synchLock and tandem-safe arbitration in SystemC models for concurrency and shared resources
---
# Skill: SystemC synchronization

## Purpose
Service several ports from one thread, record arbitration decisions so tandem can replay them, and guard state shared between threads.

Where this code goes in `model/<block>.cppm` is in **systemc-core**. The calls on each port family are in **systemc-interfaces**.

## 1. One thread, several ports
A thread hooks one `sc_event` to several dst-side ports with `setExternalEvent(&ev)`, waits on it, and asks each port `isActive()` to find work.

### Family support
*   `setExternalEvent`, `isActive()` and `isNotActive()` exist on the dst side of `rdy_vld`, `apb`, `memory`, `req_ack`, `push_ack`, `pop_ack` and `notify_ack`.
*   On `axi_read` and `axi_write` they exist on the dst side and report the address channel, so one thread can serve several AXI subordinate ports. `axi4_stream` reports its one data channel.
*   `status`, `external_reg` and `raw` have `setExternalEvent` but no `isActive()`, so they cannot join the scan below.
    *   A `status` port fires the shared event on its first `write()`, on each later `write()` that changes the value, and on every firmware write (`reg_write_cmd`), even one that repeats the value. Compare `readNonBlocking()` with the last value the thread saw.
    *   On an `external_reg` port the hooked event fires only on `write()`, from either side, and never on a firmware write (`reg_write_cmd`). A block that owns the register blocks in `read()` instead.
    *   A `raw` port can share the event, but `read()` still blocks until a value arrives.

### Pattern
The channel keeps the event pointer, so the event must outlive the thread. Make it a member, or declare it at the top of a thread function that never returns. Hook the ports once, before the loop.

```cpp
void blk::serviceThread(void)
{
    sc_event portEvent;
    cmdIn->setExternalEvent(&portEvent);
    dataIn->setExternalEvent(&portEvent);
    while (true) {
        while (cmdIn->isNotActive() && dataIn->isNotActive()) {
            wait(portEvent);
        }
        if (cmdIn->isActive()) {
            cmdSt cmd;
            cmdIn->pushReceive(cmd);
            // ...
            cmdIn->ack();
        } else {
            dataSt data;
            dataIn->read(data);
            // ...
        }
    }
}
```

Which ports are active when the thread wakes depends on timing. In a block that runs in tandem, pass the choice through `arb()` before servicing it, as in the `arb` example in section 2.

## 2. `synchLock`
`synchLock<T>` (default `T = uint64_t`) is a mutex that also records decisions for tandem. Outside tandem, `lock()` and `unlock()` are a plain mutex and `arb(v)` returns `v`. Tandem is an A2C Pro feature. There, two copies of a block run side by side. The first copy to create a lock records each `lock()` and `arb()` value, and the second copy replays them in the same order.

### Creating a lock
Declare a member and initialize it in the constructor's initializer slot:

```cpp
// block implementation members
std::shared_ptr<synchLock<>> stateLock;

// constructor initializers
        ,stateLock(synchLockFactory<>::getInstance().newLock(getAltName(), "stateLock"))
```

*   `getAltName()` is the instance's hierarchical name without the tandem level, so both tandem copies build the same key and the factory pairs them.
*   Lock names must be unique within a block instance. In base a repeated name asserts. In A2C Pro it pairs the two locks as if they were tandem copies.
*   For a non-integral `T`, the factory logs values with `T::prt()`, so `T` must have one.

### `lock` and `unlock`
*   `lock(v)` takes the mutex. In tandem, the second copy waits until the first copy's next recorded value equals `v`. The value is the match key, not a debug label, so give each call site its own value.
*   `unlock()` takes no argument. There is no RAII guard, so unlock on every path out.

```cpp
stateLock->lock(LOCK_SITE_SCHEDULE);
writesInFlight++;
stateLock->unlock();
```

`LOCK_SITE_SCHEDULE` is a constant the block defines, one per call site.

### `arb`
*   `arb(v)` records the winner your code chose. It adds no fairness. Outside tandem it returns `v` at once. In tandem, the second copy waits for the first copy's value and returns it, so both copies take the same branch.
*   Choose the winner with plain code that models the RTL policy, priority or round-robin, then pass it through `arb()` and branch on the result.
*   Use `arb()` wherever the decision depends on timing.

`srcArb` is a second `synchLock<>` created as above. Keep `arb()` and `lock()` on separate locks, because in tandem one lock's `lock()` and `arb()` calls share a single replay queue. `SRC_*` are constants the block defines.

```cpp
uint64_t winner = SRC_NONE;
if (cmdIn->isActive()) {
    winner = SRC_CMD;
} else if (dataIn->isActive()) {
    winner = SRC_DATA;
}
winner = srcArb->arb(winner);
switch (winner) {
    case SRC_CMD:  /* service cmdIn */  break;
    case SRC_DATA: /* service dataIn */ break;
    default: break;
}
```
