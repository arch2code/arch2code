---
name: systemc-to-rtl
description: Convert a SystemC behavioral model to a SystemVerilog RTL implementation following arch2code patterns. Use when implementing RTL from a model or converting C++ to SV.
---
# Skill: SystemC to RTL conversion

## Purpose
Convert a SystemC model (`model/<block>.cppm`) into synthesizable SystemVerilog (`rtl/<block>.sv`) within arch2code.

## References
*   `rtl-core.md` owns flop macros, clock domains, FSMs, naming and package imports. Follow it for every flop and FSM you write.
*   `rtl-interfaces.md` covers the interface signals and the generated memory instances.
*   `rtl-patterns.md` has the pipeline, interpolation, saturation, rounding and memory-sequencing patterns this skill points to.
*   `rtl-registers.md` covers register ports.

## Prerequisites
1.  Read `model/<block>.cppm` for the algorithm, the fixed-point math and the control flow.
2.  Read `rtl/<block>.sv`. Its generated region already has the ports, package imports, interface instances and memory instances. If the file is missing, create it with `make newmodule` (`manage-build.md`).
3.  Map each model port or member to its RTL counterpart:

| Model | RTL |
| :--- | :--- |
| `rdy_vld` input, `port->read()` | `rdy_vld_if.dst` |
| `rdy_vld` output, `port->write()` | `rdy_vld_if.src` |
| `status` input, `readNonBlocking()` | `status_if.dst`, read `.data` |
| Owned `rw` register, `reg.read()` | `status_if` instance, read `<reg>.data` |
| Owned memory, `hwMemory` `read(i)` / `write(i, v)` | generated `memory_if` instance named after the memory |
| `memory` port, `port->request(isWrite, addr, data)` | `memory_if.src` port |

## Conversion workflow

### 1. Plan the pipeline
A model often handles one transaction per loop iteration in zero time. RTL has to spread the work over cycles.
*   Break deep math into stages. `(a+b+c+d)/4` becomes `sum1 = a+b` and `sum2 = c+d`, then `total = sum1 + sum2`, then the divide (see step 5 for signed values).
*   A heavy calculation at a batch boundary, such as end of frame, cannot finish in one cycle. Serialize it with an FSM (`rtl-core.md`), for example `RDY`, `CALC1`, `CALC2`, `DONE`.

### 2. Declare pipeline registers
Use the `_INST` flop macros. `` `DFF_INST(type, name) `` declares `name`, the flop output, and `n_name`, which you drive.

```systemverilog
`DFF_INST(logic,   stg1Vld)
`DFF_INST(dataT,   stg1Data)
`DFF_INST(resultT, stg2Result)
```

### 3. Write the next-state logic
Give every `n_*` signal a default at the top of the `always_comb`, then override it:

```systemverilog
always_comb begin
    n_stg1Vld  = inPort.vld;
    n_stg1Data = stg1Data;
    if (inPort.vld) begin
        n_stg1Data = inPort.data;
    end
    n_stg2Result = stg1Data * coeff;
end
```

### 4. Memory access
A model's `request()` or `read(i)` returns at once. In RTL a read drives `addr` and `enable` in one cycle, and `read_data` is valid the next.
*   Make each sequential read one FSM state, and consume its data one cycle later. `rtl-patterns.md` (FSM-sequenced memory reads) has the paired-FSM pattern.
*   If the model reads one of two memories depending on a condition, drive both ports with the same address and select with `enable`:

```systemverilog
memA.addr   = targetAddr;
memA.enable = selectA;
memB.addr   = targetAddr;
memB.enable = ~selectA;
// one cycle later, with selectA delayed to match:
result = selectAD1 ? memA.read_data.val : memB.read_data.val;
```

The generator instantiates the memories from YAML, including `memory_dp_2clk` for a memory whose ports run on two clocks. Never hand-write a memory instance. `rtl-interfaces.md` explains how the YAML picks it.

### 5. Types and math
*   Use the types from the generated package imports. Never write a package import by hand. If a name your logic uses is not imported, add `--importPackages` (`rtl-core.md`).
*   Convert C++ `int64_t` fixed-point math to explicit `logic signed [W-1:0]` types.
*   C++ `>>` on a signed type keeps the sign. Use `>>>` on signed values and `>>` on unsigned ones.
*   C++ `/` truncates toward zero. `>>>` rounds toward minus infinity, so the two differ for negative values. For a power-of-two divide of a value that can be negative, match what the model does. If the model divides, add `2**N - 1` to a negative value before shifting.
*   If the model uses rounding or saturation helpers, write equivalent SV functions (`rtl-patterns.md`, "Saturation and clipping" and "Rounding functions").
*   If the model picks an algorithm from a parameter, use `generate if`. If it switches at run time on a register value, use a mux in `always_comb`.
*   Replace a division by a constant with a multiply by a precomputed reciprocal:

```systemverilog
// value is 18 bits
typedef logic [17:0] multInT;
typedef logic [35:0] multOutT;
typedef logic [16:0] resultT;  // value/3 needs 17 bits
localparam int RECIP_SHIFT = 19;  // input width + 1
localparam multInT RECIP_THIRD = multInT'((2**RECIP_SHIFT + 2) / 3);  // rounded up
multOutT product;  // full product width, so the multiply does not truncate
assign product = value * RECIP_THIRD;
assign result  = resultT'(product >> RECIP_SHIFT);
```

Round the reciprocal up and shift by at least the input width plus one. A larger divisor can need a bigger shift. Check the result against `/` over the whole input range.

*   Replace a division by a variable with a reciprocal lookup table in a `case` statement.
*   Model index arithmetic with shift and mask becomes bit slicing: `pos >> LOG2` is `pos[MSB:LOG2]`, and `pos & (SIZE-1)` is `pos[LOG2-1:0]`. Declare these as combinational intermediates.
*   A model that computes an interpolation once per region becomes a per-cycle slope accumulator in RTL (`rtl-patterns.md`, "Piecewise-linear interpolation").
*   Several sequential multiplies can share one registered multiplier, with an FSM loading new operands each cycle (`rtl-patterns.md`, "FSM-sequenced memory reads").
*   A model `for` loop that sums parallel values becomes a lane-reduction tree: sum the lanes, then add to the accumulator (`rtl-patterns.md`, "Parallel-lane reduction").

### 6. Registers
The model reacts to register writes with events: `setExternalEvent` and `readNonBlocking()` on a `status` port, or `registerEvent` and `read()` on an owned `hwRegister`. RTL reads `<reg>.data` combinationally every cycle:

```systemverilog
`DFF_INST(logic, modeActive)
always_comb begin
    n_modeActive = (cfgReg.data.mode == ACTIVE);
end
```

### 7. Drive the outputs

```systemverilog
assign outPort.vld  = finalStageVld;
assign outPort.data = finalStageData;
```

When `outPort.rdy` is low, the last stage cannot hand off its data. Either hold every stage while `outPort.rdy` is low and drive `inPort.rdy` from it, or tie `inPort.rdy = 1'b1` only when the downstream block accepts every cycle.

## Rules
*   Never edit between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END`.
*   Use a flop macro for every flop. Use the bare form on the default clock and `_DOM` on any other clock (`rtl-core.md`).
*   Use `logic` and `always_comb`.
