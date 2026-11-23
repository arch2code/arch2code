---
name: systemc-interfaces
description: Guide for calling interface ports (rdy_vld, push_ack, pop_ack, req_ack, notify_ack, apb, ahb, memory, axi_read, axi_write, axi4_stream, status, external_reg, raw) in SystemC models, and for which ports a --delay run delays
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

### Register array ports
A child that takes a whole array register (`count:`, a `registerConnections:` row without `index:`) gets an `sc_vector` of ports. A child that takes one element (`index: k`) gets a plain port. A container that owns the array and gives it to children holds an `sc_vector` of channels. A leaf that owns the array and uses it itself holds `std::array< hwRegister<...>, N >` and no channels, as `blockA` in `examples/apbDecode` does. From `examples/mixed`:

```cpp
// blockFBase: the whole array
sc_vector< status_in< dRegSt > > rwArr;
// blockDBase: element 2 of rwArr
status_in< dRegSt > rwArr;
// blockB, the owner
sc_vector< status_channel< dRegSt > > rwArr;

// blockB constructor: the whole form binds the vector, the element form binds one channel
uBlockF0->rwArr.bind(rwArr);
uBlockD->rwArr(rwArr[2]);
```

*   Call an element as `rwArr[i]->read()`. Each element is its own `status` or `external_reg` port, with the calls in the table below.
*   Read a `status` element with `rwArr[i]->readNonBlocking()` where the block decides, as for a scalar port. No thread waits on its changes (**review-model** section 3). `blockF` checks every element of `rwArr` when firmware writes its `extFArr`.
*   An `external_reg` element the block answers needs its own thread blocked in `read()`. Spawn one per element in the constructor, as `blockD` does for `extArr`:

    ```cpp
    for (size_t i = 0; i < REGARR_N; i++) {
        sc_spawn([this, i]() { extModel(i, extArr[i]); }, sc_gen_unique_name("extModel", false));
    }
    ```

    Copy only the per-element threads from `blockD`. Its `extRwTrack` thread waits on `rwArr->read()`, a `status` change, which breaks **review-model** section 3.

*   See **systemc-core** for an owned array.

## Calls per family
"Src" is the side that starts a transaction. "Dst" is the side that answers it.

| Family | Src side | Dst side |
| :--- | :--- | :--- |
| `rdy_vld` | `write(v)` | `read(v)` |
| `push_ack` | `push(v)` | `pushReceive(v)`, then `ack()` |
| `pop_ack` | `pop(v)` | `popReceive()`, then `ack(v)` |
| `req_ack` | `req(reqV, ackV)` | `reqReceive(reqV)`, then `ack(ackV)` |
| `notify_ack` | `notify()` | `waitNotify()`, then `ack()` |
| `apb` | `request(isWrite, addr, data)` (a write is posted); `requestWithResponse(...)` waits and returns `PSLVERR` | `reqReceive(isWrite, addr, data)`, then `complete(data, slverr)`; required for reads and response-aware writes, ignored for posted writes |
| `ahb` | As `apb`; `requestWithResponse(...)` returns the AHB ERROR response | As `apb` |
| `memory` | `request(isWrite, addr, data)` | `reqReceive(isWrite, addr, data)`, then `complete(data)` on reads only |
| `axi_read` | `sendAddr(a)`, `receiveData(r)` | `receiveAddr(a)`, `sendData(r)` |
| `axi_write` | `sendAddr(a)`, `sendData(d)`, `receiveResp(b)` | `receiveAddr(a)`, `receiveData(d)`, `sendResp(b)` |
| `axi4_stream` | `sendInfo(i)` | `receiveInfo(i)` |
| `status` | `write(v)` | `readNonBlocking()` or `read()`, see below |
| `external_reg` | `reg_write_cmd(v)`, `readNonBlocking()`, see below | `read(v)`, `update_mirror(v)`, see below |
| `raw` | `write(v)` | `read(v)` |

Multi-cycle bursts (`writeClocked`, `readClocked`, `sendDataCycle`) are in **systemc-patterns**.

### `status`
*   `status` carries state, never control. A `status` port between two blocks is a warning sign. It usually means the design is not transactional. Check it against `design-architecture.md` before you use it. It keeps only the latest value, so writes in one delta merge into one wake and an unchanged write raises no event. Never use it between blocks for busy, done, grant, interrupt, count or toggle signals, or for anything where the consumer must observe every change. A value the consumer needs only as it stands when read, such as a mode, enable or lock, is correct as `status` even when it gates a decision. A level that crosses the hardware/firmware edge, such as an interrupt line, may be `status` when its owner also sends the level's value whenever no message is out and the value differs from the last one sent. `design-architecture.md`, section "`status` carries state, never control", gives the transactional replacements.
*   `readNonBlocking()` samples the current value. A model reads `status` this way, where it makes the decision. Only the one block that turns an unclocked boundary pin input, or a level that only rises until reset, into messages waits on `read()` (**review-model** section 3).
*   `read()` blocks until a `write()` or a firmware write. A `write()` that repeats the current value raises no event, but the first `write()` always does, even when it matches the initial value. The initial value itself raises no event, so a thread that needs it at start-up samples it with `readNonBlocking()` first. `read()` can return the value it returned last, so compare with the last value seen.
*   `setExternalEvent(&ev)` replaces the port's own event, so `read()` then also returns when another port fires `ev`. There is no `isActive()`.

### `external_reg`
*   **Dst side, the block that owns the register.**
    *   `read(v)` blocks until firmware writes and returns the written value. A write made while the owner is not in `read()` waits for its next call.
    *   The owner's next `read()` call completes the write. In the RTL the bus never waits for the owner, and firmware reads back what the owner shows one clock after the write.
    *   `update_mirror(v)` publishes the value firmware reads back, without waking `read()`.
    *   The thread that waits in `read()` publishes the write's read-back value with `update_mirror(v)` before it returns to `read()`. A publish of an unchanged value is fine. Slow work may go to a queue or another thread, which publishes again when the work is done.
    *   Give each `external_reg` port its own thread. Between two `read()` calls that thread never waits on another port, on firmware or on time, because firmware's write stays open until the thread is back in `read()`.
    *   `reg_write(v)` also wakes `read()`, so do not use it to publish from a block that loops on `read()`.
*   **Src side.** This is normally the generated register handler. It issues `reg_write_cmd(v)` and reads back with `readNonBlocking()`. `reg_write_cmd(v)` returns when the owner completes the write, so a read-back after it sees the owner's value. A test driver emulating firmware uses `reg_write_cmd`. `write()` never wakes the owner's `read()`.

### `raw`
`raw` is a last resort. `read()` blocks until a value arrives, and `write()` blocks until the reader takes the value. Use it only at a design boundary to legacy or external IP that has a free-running data bus and no ready, valid or ack wires. Between arch2code blocks, use a handshaked family, and confirm with the user before proposing `raw`. The `raw` entry under "Interfaces & Interface Types" in `ARCH2CODE_AI_RULES.md` explains why.

Interfaces outside this table come from A2C Pro (`builder/pro/interfaces/`) or the user. Read their channel header for the calls.

## Timed delays
`--delay` and `--delayMode` insert delays into a block's interface calls. They exist to expose ordering problems between interfaces in timed runs and in tandem (A2C Pro). They do not model hardware latency.

The YAML decides which channels take a delay:

| Interface type | Delay |
| :--- | :--- |
| `status`, `memory`, `raw`, `external_reg` (`timing: fixed`) | Never. The channel ignores `setTimed`. |
| `rdy_vld`, `axi4_stream` | Yes, unless backpressure is off on any port the channel joins. |
| Every other type | Always. |

RTL on the far side of a channel that ignores `setTimed` cannot wait for a delayed call, so a delay there loses beats or accesses. For a Pro or project interface type, read `timing:` and `backpressure:` in its `_if.yaml`.

A delay run logs each channel that ignores `setTimed` once, with the reason:

```text
blockB.blockB_rwD:setTimed(10ns) ignored: fixed timing
producer.consumer_video:setTimed(10ns) ignored: no backpressure
```

Turn backpressure off when nothing may stall the stream. Either the producer ignores `rdy` (`tready` for `axi4_stream`), or the consumer always holds it high, as in a valid-only video stream. Set it on the `interfaces:` entry:

```yaml
interfaces:
  video_rgb_stream:
    interfaceType: rdy_vld
    desc: "RGB video, valid only"
    backpressure: false
    structures:
      - {structure: rgb_st, structureType: data_t}
```

*   Other interface types reject the key at `make db`.
*   A `ports:` row overrides the entry for that port.
*   A channel takes the delay only if every port it joins has backpressure on.
*   A container port has backpressure off when the child port it maps to has it off, at any depth.

An excludeInst testbench builds the channels between itself and the DUT in `<DUT>Channels`. Those channels see only the DUT's ports, not the peers in the External, so set the value on the `interfaces:` entry or on the DUT's `ports:` row.

Nothing delays a channel with backpressure off, so gaps between beats have to come from the testbench source.

Generated code passes the value to the channel constructor, `BACKPRESSURE_ALLOWED` or `BACKPRESSURE_NONE`. A `rdy_vld` or `axi4_stream` channel constructed by hand in user code takes the same required argument: `rdy_vld_channel<data_st> ch("ch", "blk", BACKPRESSURE_NONE);`.

The generated `setTimed` sets every port and then calls `setTimedLocal`. The YAML covers the usual cases. Override `setTimedLocal` only for a port whose behavior depends on the test configuration, such as a `rdy_vld` port whose RTL peer ignores `rdy` in one `--cfg` mode. It can remove a delay but cannot restore one on a channel that ignores `setTimed`. In an RTL run the block whose `setTimed` the run calls is the Verilator wrapper, `verif/<block>_hdl_sc_wrapper.h`, which derives from the block's base class and not from the model, so the override goes in the wrapper's user region. In a model run it goes in the model:

```cpp
// Local override of the interface delays
void setTimedLocal(int nsec, timedDelayMode mode) override {
    // In some --cfg modes the RTL sink ignores rdy on pix_out, so it cannot wait
    // for a delayed write. m_sinkIgnoresRdy is this block's own flag, set from
    // the test configuration.
    if (m_sinkIgnoresRdy) {
        pix_out->setTimed(0, TIMED_DELAY_FIXED_INIT);
    }
}
```

An existing `setTimedLocal` override that zeroes a `memory`, `status`, `raw` or `external_reg` port is now redundant. Remove it.

A block that forwards `setTimed` to the memories it owns, as in `mems.setTimed(nsec, mode)`, delays its own memory accesses. Owned memories are block members, not channels, so `timing: fixed` does not stop their delay.

## Shared events
Servicing several ports from one thread uses `setExternalEvent` and `isActive()`. **systemc-synchronization** lists which families support them and gives the pattern.
