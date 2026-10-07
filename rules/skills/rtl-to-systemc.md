---
name: rtl-to-systemc
description: Convert a SystemVerilog RTL implementation to a SystemC behavioral model. Use when creating a model from RTL or verifying logic in SystemC.
---
# Skill: RTL to SystemC conversion

## Purpose
Write a behavioral SystemC model (`model/<block>.cppm`) that matches an existing SystemVerilog block (`rtl/<block>.sv`). The model runs fast functional simulation, so it reproduces the block's function and transactions, not its pipeline.

## Prerequisites
1. Read `rtl/<block>.sv` for its pipeline depth, math and control.
2. Read `model/<block>.cppm`. Its ports are declared in the generated `base/<block>Base.cppm`. The class is a `template<typename Config>` class only when the block declares its own `params:`. **systemc-core** covers the file layout and where hand-written code goes.

## Conversion workflow

### 1. Choose the thread structure
*   A simple block is one `SC_THREAD` with a `while (true)` loop.
*   A buffering block splits into a writer thread and a reader thread. Hand work between them with a flag plus an event, or with an `sc_fifo`. See [Example: data buffer](#example-data-buffer).

### 2. Map interfaces
*   RTL ports become port calls. **systemc-interfaces** gives the calls for each family.
*   `readClocked` and `writeClocked` are only for `rdy_vld` multi-cycle bursts. See **systemc-patterns**.
*   Registers: see [Registers](#registers).
*   Memories: see [Memories](#memories).

### 3. Model the function
Do not model pipeline stages cycle by cycle unless latency matching needs it. An RTL FSM that walks `RDY` -> `CALC` -> `DONE` over 20 cycles becomes one C++ calculation at the batch boundary.

### 4. Match the math bit for bit
*   Use the arch2code-generated types. The generated regions already import the context modules the ports use. **systemc-core** shows how to import a context only the body uses.
*   Use `int64_t` for intermediates, and replicate shifts and masks exactly.
*   Replace a parallel-lane partial-sum tree with a plain `for` loop sum.
*   Clamp with an explicit type, because the literals are `int`: `std::clamp<int64_t>(val, 0, MAX)`. A floor clamp `(a > b) ? (a - b) : 0` stays as written.
*   Match the RTL's rounding exactly. The `roundDiv4` in **rtl-patterns** rounds half to even:

    ```cpp
    inline int64_t roundDiv4(int64_t sum)
    {
        int64_t q = sum >> 2;
        int64_t r = sum & 3;
        return (r == 3 || (r == 2 && (q & 1))) ? q + 1 : q;
    }
    ```

### 5. Algorithm selection
RTL that picks logic with `generate if (ALGO == 1)` becomes a C++ branch on the same parameter. Use `if constexpr` when the parameter is a compile-time constant.

### 6. Logging
```cpp
log_.logPrint(std::format("in {} result {}", inVal, res), LOG_DEBUG);
```
Verbosity rules are in **systemc-core**.

### 7. Verify
Build and run the model with `make run` (see **manage-build**). With A2C Pro, prove equivalence against the RTL with **run-tandem**.

## Registers
RTL reads a register's value combinationally. Check how the model receives it.
*   An `hwRegister` member in the generated class region is a register the block owns. Read it as **systemc-core** section 3 describes.
*   A `status_in` port in `base/<block>Base.cppm` carries a read-write register the register handler holds. Sample it once with `readNonBlocking()`, then loop on `read()`, which wakes on each firmware write.
*   A `status_out` port carries a read-only register. The block drives the value firmware reads with `write(v)`.
*   An `external_reg` port carries a register the block implements itself. The handler forwards firmware accesses to it. Wait for firmware writes with `read(v)` and publish the read-back value with `update_mirror(v)`.

**systemc-interfaces** has the full call rules.

A listener thread caches derived values in members, so the processing thread never blocks on configuration:

```cpp
void blk::configListener(void)
{
    sc_event configEvent;
    configReg.registerEvent(&configEvent);
    while (true) {
        modeActive = (configReg.read().mode == MODE_ACTIVE);
        wait(configEvent);
    }
}
```

An RTL write pulse on `external_reg_if` becomes a thread that blocks in `read()`:

```cpp
void blk::cmdListener(void)
{
    while (true) {
        cmdRegSt cmd;
        cmdReg->read(cmd);
        cmdPending = cmd.trigger;
    }
}
```

## Memories
A memory reached through a `memory` port (`memory_out`, `memory_if.src` in RTL) uses `port->request(isWrite, addr, data)`. A read returns the value in `data`. A write sends `data`.

An RTL FSM that sequences memory reads over several cycles becomes sequential calls in a helper:

```cpp
memAddrSt a0, a1;
a0.index = (row << COL_BITS) | col;
a1.index = (rowNext << COL_BITS) | col;
memDataSt d0, d1;
lineMem->request(false, a0, d0);
lineMem->request(false, a1, d1);
```

Replicate the RTL address encoding exactly, so `{row, col}` becomes `(row << COL_BITS) | col`. The address and data field names come from the structures in the YAML.

## Position and counter tracking
RTL decomposes an index by bit slicing. The model uses the same shift and mask.

| RTL bit slice | SystemC |
| :--- | :--- |
| `pos[MSB:LOG2]` (block index) | `pos >> LOG2` |
| `pos[LOG2-1:0]` (offset in block) | `pos & (BLOCK_SIZE - 1)` |

## Piecewise-linear interpolation
RTL accumulates a slope every cycle across a block region. The model computes the start value and slope once per block boundary, then steps through the elements:

```cpp
loadBlockFactors(blockX, blockY, weight, factor, slope);
for (int i = 0; i < ELEMENTS_PER_CYCLE; i++) {
    // use factor
    factor += slope;
}
```

## Example: data buffer
RTL writes a RAM at `wr_addr` and starts reading once `wr_addr` passes a threshold. An immediate `notify()` is lost when the other thread is not yet waiting, so pair the event with a flag:

```cpp
void blk::inputThread(void)
{
    while (true) {
        dataSt data;
        dataIn->read(data);
        store(data);
        if (enoughData()) {
            bufferReady = true;
            bufferEvent.notify();
        }
    }
}

void blk::processThread(void)
{
    while (true) {
        while (!bufferReady) {
            wait(bufferEvent);
        }
        bufferReady = false;
        // process buffered data
    }
}
```

## Rules
*   Never edit `*Base.cppm` files or generated regions.
*   Reuse the generated types. Do not redefine a type the YAML already defines.
