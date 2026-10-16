---
name: systemc-patterns
description: Reference for common SystemC implementation patterns including producer-consumer, register access, multi-interface handling, multi-cycle bursts and resource tracking
---
# Skill: SystemC patterns

## Purpose
Pick the established pattern for a common modelling problem, and find the skill that owns its details.

## 1. Producer-consumer
The producer calls `port->write(v)` and the consumer calls `port->read(v)` on a `rdy_vld` port. Both calls block, so neither loop needs its own `wait()`. Calls for the other families are in **systemc-interfaces**.

## 2. Register access
The generated register handler, owned registers and memories, and the one allowed hand-written register thread are in **systemc-core** section 3.

## 3. One thread, several ports
Hook one event to several ports with `setExternalEvent` and wait on it. After a wake-up, check `isActive()` on the handshake ports.

`status`, `external_reg` and `raw` ports can share the event but have no `isActive()`. A `status` port fires it on its first `write()`, on each later `write()` that changes the value, and on every firmware write (`reg_write_cmd`). To tell whether it changed, compare `readNonBlocking()` with the last value the thread saw.

**systemc-synchronization** lists the families, the full pattern and tandem-safe arbitration.

## 4. Multi-cycle burst
A burst moves one large structure over a narrow interface as several beats.
*   The interface's YAML entry must set `multiCycleMode`, plus `maxTransferSize` where the mode needs it. Without it, `writeClocked` sends each beat as a full transaction.
*   On `rdy_vld`, the writer loops on `writeClocked(beat)` and the reader on `readClocked(beat)`.
*   On AXI, the side sending data loops on `sendDataCycle(beat)` and the receiving side on `receiveDataCycle(beat)`.
*   Do not mix beat calls and whole-transaction calls on one interface.
*   On `rdy_vld`, `getWritePtr()` and `getReadPtr()` give zero-copy access to the burst buffer. They assert when the interface has a tracker.

The `multiCycleMode` values are in `builder/base/config/schema.yaml`.

## 5. Resource tracking
A tracker tags a transaction from entry to exit and logs its progress. Allocation, logging, deallocation and tandem reference counting are in **debug**.
