---
name: rtl-to-systemc
description: Convert a SystemVerilog RTL implementation to a SystemC behavioral model. Use when creating a model from RTL or verifying logic in SystemC.
globs: "model/**/*.cpp, rtl/**/*.sv"
alwaysApply: false
---
# Skill: RTL to SystemC Conversion

## Purpose
Guide the user in creating a behavioral SystemC model (`.cpp`) that matches the functionality of an existing SystemVerilog RTL block (`.sv`). The model is used for fast, functional simulation in the arch2code environment.

## Prerequisites
1. **Read the RTL**: Analyze `rtl/<block>.sv` to understand the pipeline depth, math, and logic.
2. **Read the Model Skeleton**: Read `model/<block>.cpp`. It will have the class structure and generated ports.

## Conversion Workflow

### 1. Identify the Model Structure
- **Simple Blocks**: Use a single `SC_THREAD` (e.g., `run()` or `input_handler()`) with a `while(true)` loop.
- **Complex Blocks (Buffering)**: Split into multiple threads (e.g., `input_handler` for writing, `data_reader` for reading) and synchronize them using `sc_event` and boolean flags/FIFOs.

### 2. Map Interfaces
- **Inputs**: `rtl_port.data` -> `port->read(var)` or `port->readClocked(var)`.
- **Outputs**: `rtl_port.data` -> `port->write(var)`.
- **Registers**: `rtl_reg.data` -> See [Register Listener Pattern](#register-listener-pattern) below.
- **Memory**: See [Memory Interface Mapping](#memory-interface-mapping) below.

### 3. Implement Behavior
Do not model pipeline stages cycle-by-cycle unless necessary for latency matching. Model the **function**.

**Example:**
- **RTL**: FSM (`RDY` -> `CALC` -> `DONE`) over 20 cycles.
- **SystemC**: Perform the entire calculation instantly in C++ at the batch boundary inside the loop.

### 4. Handle Math (Bit-Accuracy)
- **Types**: Use `int32_t`, `int64_t` for intermediates.
- **Fixed-Point**: Replicate shifts (`>>>`) and bit-masks exactly.
- **Rounding**: If RTL has `round_div4`, implement a matching C++ helper:
  ```cpp
  inline int round_div4(int sum) { ... }
  ```
- **Saturation**: Explicitly check range and clamp: `std::clamp(val, 0, MAX)`.

### 5. Algorithm Selection
If RTL uses `generate if (ALGO == 1)`, SystemC should use runtime checks:
```cpp
if (ALGO == 1) {
    // Logic 1
} else {
    // Logic 2
}
```

### 6. Logging
Use `log_.logPrint` to aid debugging.
```cpp
log_.logPrint(std::format("Input: {}, Result: {}", in_val, res), LOG_DEBUG);
```

## Register Listener Pattern

RTL reads `status_if.data` combinationally (always valid). SystemC uses a dedicated listener thread with `setExternalEvent` to cache register values and react to changes:

```cpp
// Header: declare event and cached values
sc_event m_config_change_event;
bool mode_active = false;

// Dedicated listener thread (registered in constructor as SC_THREAD)
void block::config_listener(void) {
    config_reg->setExternalEvent(&m_config_change_event);
    while (true) {
        config_reg_t reg;
        config_reg->readNonBlocking(reg);
        mode_active = (reg.mode == ACTIVE);
        wait(m_config_change_event);
    }
}
```

### Conversion Rules
1. RTL `always_comb` reading `status_if.data` directly becomes a dedicated `SC_THREAD` with `setExternalEvent` + `readNonBlocking` + `wait(event)`.
2. Cache derived values (e.g., `mode_active`) as class members so the main processing thread can use them without blocking.
3. The listener thread runs independently, updating cached values whenever the register changes.

## Position/Counter Tracking

RTL uses bit-slicing for index decomposition (implicit division/modulo). SystemC uses equivalent shift/mask operations:

| RTL bit-slice | SystemC equivalent |
|---------------|-------------------|
| `pos[MSB:LOG2]` (block index) | `pos >> LOG2` |
| `pos[LOG2-1:0]` (offset in block) | `pos & (BLOCK_SIZE - 1)` |

## Piecewise-Linear Interpolation (Slope-Accumulate to Compute-Once)

RTL accumulates a slope per-cycle across a block region. SystemC computes the final value once per block boundary in a helper function, then steps through elements:

```cpp
// SystemC: compute factor and slope once per block
load_block_factors(block_x, block_y, weight, factor, slope);
// Then in the element loop:
factor += slope;  // per ELEMENTS_PER_CYCLE step
```

## Memory Interface Mapping

RTL uses `memory_if.src` ports with an FSM to sequence reads/writes over multiple cycles. In SystemC, replace the entire FSM with direct `mem->request()` calls.

### RTL Pattern (Multi-Cycle FSM)
RTL drives `memory_if` signals (`addr`, `enable`, `wr_en`, `write_data`) and reads `read_data` one cycle later. Multiple reads require an FSM to sequence addresses.

### SystemC Pattern (Blocking Calls)
Replace the entire FSM with sequential `mem->request()` calls:

```cpp
addr_t addr0, addr1;
addr0.addr = (row << COL_BITS) | col;
addr1.addr = (row_next << COL_BITS) | col;

data_t d0, d1;
mem->request(false, addr0, d0);  // false = read
mem->request(false, addr1, d1);
```

### API Reference
```cpp
mem->request(bool isWrite, const addr_t& addr, data_t& data);
```
- **Read**: `isWrite = false`. After the call, `data` contains the value read.
- **Write**: `isWrite = true`. `data` holds the value to write.

### Conversion Rules
1. **Collapse FSMs**: RTL memory read FSMs become sequential `request()` calls in a helper function.
2. **Address construction**: Replicate the RTL address encoding exactly (e.g., `{row, col}` becomes `(row << COL_BITS) | col`).
3. **Conditional access**: If RTL conditionally reads different memories, use an `if` statement:
   ```cpp
   if (select_a) {
       mem_a->request(false, addr, data);
   } else {
       mem_b->request(false, addr, data);
   }
   ```
4. **Helper functions**: Extract memory access + computation into a helper called from the main loop.
5. **Types**: Use the same struct types as defined in the package. Access fields directly (e.g., `data.val`, `addr.addr`).

## `external_reg_if` (Write-Pulse Commands)

RTL uses `external_reg_if` for single-cycle write pulses (`|write`). SystemC uses `setExternalEvent` + `readNonBlocking` in a dedicated thread:

```cpp
void block::cmd_register_thread() {
    cmd_reg->setExternalEvent(&m_cmd_event);
    while (true) {
        wait(m_cmd_event);
        cmd_t data = cmd_reg->readNonBlocking();
        cmd_flag = data.trigger;
    }
}
```

## LUT / Memory Replicas

RTL uses `N` copies of `memory_dp` (for parallel reads). SystemC uses a single shadow `std::vector` with a `reqReceive`/`complete` thread per port:

```cpp
std::vector<entry_t> lut_shadow_(LUT_DEPTH);

void block::lut_model(void) {
    while (true) {
        bool isWrite; addr_t addr; entry_t data;
        lut_port->reqReceive(isWrite, addr, data);
        if (isWrite) {
            lut_shadow_[addr.value] = data;
        } else {
            lut_port->complete(lut_shadow_[addr.value]);
        }
    }
}
```

## Accumulator / Rounding Simplification

RTL uses lane-specific `generate if` blocks and bit-manipulation rounding functions. SystemC replaces these with simple arithmetic:

| RTL | SystemC |
|-----|---------|
| Parallel-lane partial-sum tree with extra pipeline stage | Simple `for` loop sum |
| `round_div4` (banker's rounding via bit ops) | Integer rounding helper function |
| Manual bit checks for saturation | `std::clamp(val, 0, MAX)` |
| `(a > b) ? (a - b) : 0` (floor-clamp) | Same pattern or `std::max(a - b, 0)` |

## Critical Rules
- **NEVER** edit `*Base.h` files.
- **Match Types**: Use types from `*_package.sv` which are generated into `*_types.h`.
- **Events**: Use `wait(event)` to synchronize threads if buffering data.

## Example: Data Buffer
**RTL**:
- Writes to RAM at `wr_addr`.
- Reads from RAM when `wr_addr` > threshold.

**SystemC**:
```cpp
// Thread 1: Input
while(true) {
    in->read(data);
    buffer[row][col] = data;
    if (enough_data) event.notify();
}

// Thread 2: Process
while(true) {
    wait(event);
    // Process buffered data
}
```
