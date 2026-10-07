---
name: systemc-interfaces
description: Guide for calling interface ports (rdy_vld, push_ack, pop_ack, req_ack, notify_ack, apb, memory, axi_read, axi_write, axi4_stream, status, external_reg, raw) in SystemC models
---
# Skill: SystemC interfaces

## Purpose
Pick the right port call for each interface family in a SystemC model.

## References
*   `builder/base/SYSTEMC_API_USER_REFERENCE.md`, section "Communication Channels", covers every family. The channel source is `builder/base/interfaces/<type>/<type>_channel.h`, where the `_in_if` class is the dst side and the `_out_if` class is the src side.
*   Where hand-written code goes in `model/<block>.cppm`: **systemc-core**.

## Ports
*   The generator declares every port in the block's base class. Do not declare ports by hand.
*   Call a port's methods through `->`, as in `dataIn->read(v)`.
*   A register or memory the block owns is a member, not a port. See **systemc-core**.

## Calls per family
"Src" is the side that starts a transaction. "Dst" is the side that answers it.

| Family | Src side | Dst side |
| :--- | :--- | :--- |
| `rdy_vld` | `write(v)` | `read(v)` |
| `push_ack` | `push(v)` | `pushReceive(v)`, then `ack()` |
| `pop_ack` | `pop(v)` | `popReceive()`, then `ack(v)` |
| `req_ack` | `req(reqV, ackV)` | `reqReceive(reqV)`, then `ack(ackV)` |
| `notify_ack` | `notify()` | `waitNotify()`, then `ack()` |
| `apb` | `request(isWrite, addr, data)` | `reqReceive(isWrite, addr, data)`, then `complete(data)` on reads only |
| `memory` | `request(isWrite, addr, data)` | `reqReceive(isWrite, addr, data)`, then `complete(data)` on reads only |
| `axi_read` | `sendAddr(a)`, `receiveData(r)` | `receiveAddr(a)`, `sendData(r)` |
| `axi_write` | `sendAddr(a)`, `sendData(d)`, `receiveResp(b)` | `receiveAddr(a)`, `receiveData(d)`, `sendResp(b)` |
| `axi4_stream` | `sendInfo(i)` | `receiveInfo(i)` |
| `status` | `write(v)` | `readNonBlocking()` or `read()`, see below |
| `external_reg` | `reg_write_cmd(v)`, `readNonBlocking()`, see below | `read(v)`, `update_mirror(v)`, see below |
| `raw` | `write(v)` | `read(v)` |

Multi-cycle bursts (`writeClocked`, `readClocked`, `sendDataCycle`) are in **systemc-patterns**.

### `status`
*   `readNonBlocking()` samples the current value.
*   `read()` blocks until a `write()` or a firmware write. A `write()` that repeats the current value raises no event, but the first `write()` always does, even when it matches the initial value. The initial value itself raises no event, so a thread that needs it at start-up samples it with `readNonBlocking()` first. `read()` can return the value it returned last, so compare with the last value seen.
*   `setExternalEvent(&ev)` replaces the port's own event, so `read()` then also returns when another port fires `ev`. There is no `isActive()`.

### `external_reg`
*   **Dst side, the block that owns the register.**
    *   `read(v)` blocks until firmware writes and returns the written value.
    *   `update_mirror(v)` publishes the value firmware reads back, without waking `read()`.
    *   `reg_write(v)` also wakes `read()`, so do not use it to publish from a block that loops on `read()`.
*   **Src side.** This is normally the generated register handler. It issues `reg_write_cmd(v)` and reads back with `readNonBlocking()`. A test driver emulating firmware uses `reg_write_cmd`. `write()` never wakes the owner's `read()`.

### `raw`
`raw` is a last resort. `read()` blocks until a value arrives, and `write()` blocks until the reader takes the value. Use it only at a design boundary to legacy or external IP that has a free-running data bus and no ready, valid or ack wires. Between arch2code blocks, use a handshaked family, and confirm with the user before proposing `raw`. The `raw` entry under "Interfaces & Interface Types" in `ARCH2CODE_AI_RULES.md` explains why.

Interfaces outside this table come from A2C Pro (`builder/pro/interfaces/`) or the user. Read their channel header.

## Shared events
Servicing several ports from one thread uses `setExternalEvent` and `isActive()`. **systemc-synchronization** lists which families support them and gives the pattern.
