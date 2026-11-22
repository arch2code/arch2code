---
name: systemc-synchronization
description: Guide for using shared events and arbitration in SystemC models, to service several ports from one thread and choose between them as the RTL does
---
# Skill: SystemC synchronization

## Purpose
Service several ports from one thread, and choose between them the way the RTL does. Guard shared state with a busy flag or an `sc_event`. In A2C Pro, **systemc-synchlock** records these choices for Tandem.

Where this code goes in `model/<block>.cppm` is in **systemc-core**. The calls on each port family are in **systemc-interfaces**.

## 1. One thread, several ports
A thread hooks one `sc_event` to several dst-side ports with `setExternalEvent(&ev)`, waits on it, and asks each port `isActive()` to find work.

### Family support
*   `setExternalEvent`, `isActive()` and `isNotActive()` exist on the dst side of `rdy_vld`, `apb`, `memory`, `req_ack`, `push_ack`, `pop_ack` and `notify_ack`.
*   On `axi_read` and `axi_write` they exist on the dst side and report the address channel, so one thread can serve several AXI subordinate ports. `axi4_stream` reports its one data channel.
*   `status`, `external_reg` and `raw` have `setExternalEvent` but no `isActive()`, so they cannot join the scan below.
    *   A `status` port fires the shared event on its first `write()`, on each later `write()` that changes the value, and on every firmware write (`reg_write_cmd`), even one that repeats the value. Compare `readNonBlocking()` with the last value the thread saw. Only the one block that turns an unclocked boundary pin input, or a level that only rises until reset, into messages hooks a `status` port this way (**review-model** section 3).
    *   On an `external_reg` port the hooked event fires only on `write()`, from either side, and never on a firmware write (`reg_write_cmd`). A block that owns the register blocks in `read()` instead. The thread that waits in `read()` does no other blocking work. It hands each write to a queue or a member and returns to `read()`.
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

Which ports are active when the thread wakes depends on timing. Choose between them as in section 2.

## 2. Arbitration
The order in which a thread services active ports is a decision. Make it where the RTL arbitrates, with plain code that models the RTL policy, such as priority or round-robin, and branch on the result. Never leave it to thread scheduling order. `src_t` is a YAML enum with the values `SRC_*`, because the RTL declares the grant too.

```cpp
src_t winner = SRC_NONE;
if (cmdIn->isActive()) {
    winner = SRC_CMD;
} else if (dataIn->isActive()) {
    winner = SRC_DATA;
}
switch (winner) {
    case SRC_CMD:  /* service cmdIn */  break;
    case SRC_DATA: /* service dataIn */ break;
    default: break;
}
```

In A2C Pro, pass the winner through `synchLock` `arb()` before the `switch` so Tandem replays the decision (**systemc-synchlock**, A2C Pro).
