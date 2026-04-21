---
name: systemc-to-rtl
description: Convert a SystemC behavioral model to a SystemVerilog RTL implementation following arch2code patterns. Use when implementing RTL from a model or converting C++ to SV.
---
# Skill: SystemC to RTL Conversion

## Purpose
Guide the user in converting a high-level SystemC model (`.cpp`) to a synthesizable SystemVerilog implementation (`.sv`) within the arch2code framework.

## Prerequisites
1. **Read the SystemC Model**: Analyze `model/<block>.cpp` to understand the algorithm, math (fixed-point), and control flow.
2. **Read the RTL Skeleton**: Read `rtl/<block>.sv`. It will have generated ports and imports.
3. **Identify Interfaces**:
   - **Stream Inputs**: `rdy_vld_if.dst` (SystemC: `port->read()`)
   - **Stream Outputs**: `rdy_vld_if.src` (SystemC: `port->write()`)
   - **Registers**: `status_if.dst` (SystemC: `reg->readNonBlocking()`)
   - **Memory**: `memory_if.src` (SystemC: `mem->request()`)

## Conversion Workflow

### 1. Plan the Pipeline
SystemC often processes one transaction per loop iteration. RTL requires pipelining to meet timing.
- **Deep Pipelines**: Break complex math (e.g., `(a+b+c+d)/4`) into multiple stages:
    - Stage 1: `sum1 = a+b`, `sum2 = c+d`
    - Stage 2: `total = sum1 + sum2`
    - Stage 3: `result = total >> 2`
- **FSMs**: If the SystemC model performs a heavy calculation at a batch boundary (e.g., end-of-transaction, end-of-frame), it CANNOT be done in one cycle. Use a **State Machine** to serialize the math (e.g., `RDY` -> `CALC_STEP_1` -> `CALC_STEP_2` -> `DONE`).

### 2. Declare Pipeline Registers (`DFF_INST`)
Use `DFF_INST(type, name)` which creates:
- `name`: The register output (current state).
- `n_name`: The register input (next state, you must drive this).

```systemverilog
`DFF_INST(data_t, stg1_data)
`DFF_INST(logic, stg1_vld)
```

### 3. Implement Logic (`always_comb`)
Write combinational logic to calculate next states (`n_*`).

```systemverilog
always_comb begin
    n_stg1_vld = 1'b0;
    if (in_port.vld) begin
        n_stg1_data = in_port.data;
        n_stg1_vld = 1'b1;
    end
    n_stg2_result = stg1_data * coeff;
end
```

### 4. Memory Interface Conversion

SystemC `mem->request()` calls are blocking and instant. RTL must drive `memory_if` signals across clock cycles with an FSM.

#### SystemC Pattern (Instant Reads)
```cpp
mem->request(false, addr0, data0);  // blocking, data in data0 immediately
mem->request(false, addr1, data1);
```

#### RTL Pattern (FSM-Sequenced Reads)
Each `request()` becomes one FSM state. Drive `addr` and `enable` in one cycle; `read_data` is valid the next cycle.

```systemverilog
if (1) begin: mem_read_fsm
    typedef enum logic [1:0] {RD0, RD1, RD2, RD3} statesT;
    `include "fsmDefs.svh"
    always_comb begin
        nState = state;
        mem.write_data = '0;
        mem.wr_en = 1'b0;
        mem.addr = base_addr;
        mem.enable = 1'b0;

        `fsmCase
            `fsmState(RD0) begin
                if (trigger_condition) begin
                    mem.addr = addr0;
                    mem.enable = 1'b1;
                    `nxtState(RD1)
                end
            end
            `fsmState(RD1) begin
                mem.addr = addr1;
                mem.enable = 1'b1;
                `nxtState(RD2)
            end
            // ... RD2, RD3 follow same pattern
        `fsmEndCase
    end
end: mem_read_fsm
```

#### Consuming Read Data
Read data from cycle N is available in cycle N+1. Use a **second FSM** or pipeline stage to consume `mem.read_data` one cycle after the address was driven. See `rtl-patterns.md` (Paired FSMs).

#### Conditional Memory Access
If SystemC conditionally reads from different memories, RTL drives all memory ports in parallel with conditional `enable`:

```systemverilog
mem_a.addr = target_addr;
mem_a.enable = select_a;
mem_b.addr = target_addr;
mem_b.enable = ~select_a;
result = select_a ? mem_a.read_data.val : mem_b.read_data.val;
```

#### Scoped FSMs with `if (1) begin: label`
Use `if (1) begin: <label>` blocks to scope each FSM. This allows multiple FSMs in the same module, each with their own `statesT` enum and `state`/`nState` signals.

### 5. Handle Types and Math
- **Typedefs**: Use `import <block>_package::*;` types.
- **Fixed-Point**: Convert C++ `int64_t` math to explicit SV `logic signed [W:0]`.
- **Arithmetic Shift Right**: C++ `>> N` on signed types preserves sign. In RTL, use `>>>` for signed values (arithmetic shift) vs `>>` (logical shift, zero-fills MSBs):
  ```systemverilog
  n_result = result_t'(signed_value >>> SHIFT_AMOUNT);
  ```
- **Rounding/Saturation**: If C++ uses rounding or saturation helpers, implement equivalent SystemVerilog functions. See `rtl-patterns.md` (Saturation/Clipping, Rounding).
- **Generators**: If the SystemC model switches algorithms based on config, use RTL `generate if` blocks.

### 5a. Bit-Slicing for Division/Modulo
SystemC uses shift/mask for index decomposition. RTL uses bit-slicing (zero cost in hardware):

| SystemC | RTL |
|---------|-----|
| `idx = pos >> BLOCK_SIZE_LOG2` | `idx = pos[MSB:BLOCK_SIZE_LOG2]` |
| `offset = pos & (BLOCK_SIZE - 1)` | `offset = {1'b0, pos[BLOCK_SIZE_LOG2-1:0]}` |

Declare these as combinational intermediate signals (no flop needed).

### 5b. Piecewise-Linear Interpolation
SystemC computes interpolation results once per block. RTL must accumulate a slope per-cycle:

**SystemC** (instant):
```cpp
left_val  = (corner00 * weight_inv + corner01 * weight) >> WEIGHT_BITS;
right_val = (corner10 * weight_inv + corner11 * weight) >> WEIGHT_BITS;
slope = (right_val - left_val) >> DIVISIONS_LOG2;
// per element step: left_val += slope;
```

**RTL** (per-cycle accumulation):
```systemverilog
if (boundary_start) begin
    n_factor = start_value;
    n_slope = (new_end_value - start_value) >>> DIVISIONS_LOG2;
end else begin
    n_factor = factor + slope;  // accumulate each cycle
    n_slope = slope;            // hold slope
end
```

### 5c. Register Interface Conversion
SystemC uses `setExternalEvent` + `readNonBlocking` in a listener thread. RTL reads `status_if.data` directly in `always_comb`:

```systemverilog
`DFF_INST(logic, mode_active)
always_comb begin
    n_mode_active = (config_reg.data.mode == ACTIVE) ? 1'b1 : 1'b0;
end
```

### 5d. Division and Reciprocals

C++ division (`/`) does not synthesize efficiently. Replace with:
- **Power-of-2 division**: Use arithmetic shift right `>>>`
- **Constant reciprocal**: Pre-compute `(2^N)/divisor` as a localparam and multiply:
  ```systemverilog
  localparam RECIP_WIDTH = 18;
  mult_in_t recip_third = (2**RECIP_WIDTH) / 3;
  result = (value * recip_third) >> RECIP_WIDTH;
  ```
- **Variable reciprocal**: Use a case-statement LUT:
  ```systemverilog
  case (divisor_in)
      8'h01: n_recip_out = 18'h20000;
      8'h02: n_recip_out = 18'h10000;
      // ... generated entries
  endcase
  ```

### 5e. Shared Multiplier via FSM

When SystemC performs multiple sequential multiplications, RTL can time-share a single DSP multiplier by loading different operands each FSM cycle. See `rtl-patterns.md` (Shared Multiplier).

### 5f. Parallel-Lane Reduction

SystemC `for` loops summing `N` parallel values become `generate if` blocks in RTL with lane-specific partial sum trees. High lane counts need an extra pipeline stage. See `rtl-patterns.md` (Parallel-Lane Reduction Trees).

### 6. Memory Instantiation (Container Level)
Memories are instantiated at the **container** module, not inside the core. The container connects `memory_dp` between the core and regs:

```systemverilog
memory_if #(.data_t(mem_data_t), .addr_t(mem_addr_t)) mem_core();
memory_if #(.data_t(mem_data_t), .addr_t(mem_addr_t)) mem_reg();

memory_dp #(.DEPTH(MEM_DEPTH), .data_t(mem_data_t)) uMem (
    .mem_portA (mem_core),
    .mem_portB (mem_reg),
    .clk (clk)
);
```

### 7. Connect Outputs
Assign the output ports to the final pipeline stage signals.

```systemverilog
assign out_port.vld = final_stage_vld;
assign out_port.data = final_stage_data;
assign in_port.rdy = 1'b1; // No backpressure
```

## Critical Rules
- **NEVER** edit between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END`.
- **ALWAYS** use `DFF_INST` for sequential logic.
- **ALWAYS** use `logic` and `always_comb`.
- **ALWAYS** import the block package.
- **Parallel Accumulation**: If summing parallel lanes, sum them first then add to the main accumulator.

## Example: Pipeline vs FSM Decision

**Pipeline (per-element processing):**
```systemverilog
`DFF_INST(result_t, prod)
always_comb n_prod = input_val * coeff;
```

**FSM (batch-boundary calculation):**
```systemverilog
typedef enum logic [1:0] {IDLE, CALC, DONE} statesT;
`include "fsmDefs.svh"
always_comb begin
    nState = state;
    `fsmCase
        `fsmState(IDLE) begin
            if (batch_done) `nxtState(CALC)
        end
        `fsmState(CALC) begin
            // multi-cycle computation...
            `nxtState(DONE)
        end
        `fsmState(DONE) begin
            `nxtState(IDLE)
        end
    `fsmEndCase
end
```
