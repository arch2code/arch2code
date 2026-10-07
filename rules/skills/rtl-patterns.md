---
name: rtl-patterns
description: Reference for common RTL implementation patterns including pipelines, FSMs, interpolation, saturation, resource sharing, and memory access sequences
---
# Skill: RTL patterns

## Purpose
Common SystemVerilog patterns for arch2code blocks. Flop macros, clock domains and FSMs are in `rtl-core.md`.

## Pipeline stages

Each stage carries `vld`, its data and the sideband metadata, such as transaction IDs, frame markers or sequence numbers:

```systemverilog
// Stage 1: Capture input
`DFF_INST(dataT, s1Data)
`DFF_INST(metaT, s1Meta)
`DFF_INST(logic, s1Vld)

always_comb begin
    n_s1Vld  = inPort.vld;
    n_s1Meta = inPort.data.meta;
    n_s1Data = inPort.data.payload;
end

// Stage 2: Process
`DFF_INST(logic, s2Vld)
`DFF_INST(metaT, s2Meta)
`DFF_INST(resultT, s2Result)

always_comb begin
    n_s2Vld    = s1Vld;
    n_s2Meta   = s1Meta;
    n_s2Result = s1Data * coeff;
end

// Stage 3: Output
`DFF_INST(outDataT, s3Data)
`DFF_INST(metaT, s3Meta)
`DFF_INST(logic, s3Vld)

always_comb begin
    n_s3Vld  = s2Vld;
    n_s3Meta = s2Meta;
    n_s3Data = clip(s2Result);
end

// Drive output
assign outPort.vld          = s3Vld;
assign outPort.data.payload = s3Data;
assign outPort.data.meta    = s3Meta;
```

Drive the output interface with `assign` from the last stage, or from an `always_comb` when one stage drives several interfaces.

## Position and counter tracking

Track a row and column position in a stream from its start and end markers. Register the end-of-group marker on each valid beat and use it as the start of the next group. Take sub-indices by bit slicing, which divides by a power of two and takes the remainder at no cost:

```systemverilog
`DFF_INST(xPosT, posX)
`DFF_INST(yPosT, posY)
`DFF_INST(logic, startOfGroup)

always_comb begin
    n_posX = posX;
    n_posY = posY;
    n_startOfGroup = startOfGroup;

    if (inVld) begin
        n_startOfGroup = inMeta.endOfGroup;
        if (inMeta.startOfFrame) begin
            n_posX = '0;
            n_posY = '0;
        end else if (startOfGroup) begin
            n_posX = '0;
            n_posY = posY + 1'b1;
        end else begin
            n_posX = posX + xPosT'(ELEMENTS_PER_CYCLE);
        end
    end
end

// Grid index and offset within the grid cell, by bit slicing
gridIdxT gridY;
gridCountT subY;
always_comb begin
    gridY = posY[MSB:GRID_SIZE_LOG2];               // posY / GRID_SIZE
    subY  = {1'b0, posY[GRID_SIZE_LOG2-1:0]};       // posY % GRID_SIZE
end
```

## Piecewise-linear interpolation (slope accumulate)

For linear interpolation across a grid or region, compute the start value and slope at the boundary, then accumulate per-cycle:

```systemverilog
`DFF_INST(factorT, interpVal)
`DFF_INST(factorT, interpSlope)

always_comb begin
    n_interpVal   = interpVal + interpSlope;  // accumulate
    n_interpSlope = interpSlope;              // hold slope
    if (boundaryStart) begin
        n_interpVal   = startValue;
        n_interpSlope = (endValue - startValue) >>> DIVISIONS_LOG2;
    end
end
```

Use `>>>` (arithmetic shift right) for signed values to preserve the sign bit. Use `>>` only for unsigned values.

`>>>` rounds toward minus infinity. If the model divides with `/`, apply the bias in `systemc-to-rtl.md` ("Types and math", the signed-division step).

## Saturation and clipping

Three common patterns:

**Signed two-sided clamp** (negative -> 0, overflow -> max, else extract):
```systemverilog
function automatic resultT saturate(input accumT accum);
    if (accum[ACCUM_W-1]) return resultT'('0);
    if (|accum[ACCUM_W-2:RESULT_WIDTH]) return resultT'(2**RESULT_WIDTH-1);
    return resultT'(accum);
endfunction
```

**Unsigned fixed-point overflow clip** (MSB check on multiply result):
```systemverilog
function automatic resultT clipMult(input multOutT multVal);
    if (|multVal[WIDTH-1:WIDTH-INTEGER_WIDTH]) return resultT'(MAX_VALUE);
    return resultT'(multVal[WIDTH-1-INTEGER_WIDTH:WIDTH-INTEGER_WIDTH-RESULT_WIDTH]);
endfunction
```

**Unsigned subtraction with floor-clamp** (prevent underflow):
```systemverilog
n_outVal = (inVal > offset) ? (inVal - offset) : resultT'('0);
```

## Rounding functions

Round half to even when dividing by 2 or by 4:

```systemverilog
localparam W_P1 = WIDTH + 1;
localparam W_P2 = WIDTH + 2;
typedef logic [W_P1-1:0] acc2T;
typedef logic [W_P2-1:0] acc4T;

function automatic resultT roundDiv2(input acc2T sum);
    return (sum[1:0] == 2'b11) ? (sum[W_P1-1:1] + 1'b1) : sum[W_P1-1:1];
endfunction

function automatic resultT roundDiv4(input acc4T sum);
    return ((sum[1:0] == 2'b11) || (sum[1:0] == 2'b10 && sum[2] == 1'b1)) ?
        (sum[W_P2-1:2] + 1'b1) : sum[W_P2-1:2];
endfunction
```

## Parallel-lane reduction

To accumulate `LANES` parallel elements, sum the lanes first, then add the sum to the accumulator. With many lanes, register the partial sums and delay `vld` and `start` by the same stage, so every lane of a beat lands in the accumulator together:

```systemverilog
`DFF_INST(accT, acc)

generate
    if (LANES == 4) begin : gen_4lane
        always_comb begin
            n_acc = acc;
            if (inVld) begin
                n_acc = (start ? '0 : acc) + element[0] + element[1] + element[2] + element[3];
            end
        end
    end else if (LANES == 8) begin : gen_8lane
        `DFF_INST(partialT, sumLo)
        `DFF_INST(partialT, sumHi)
        `DFF_INST(logic, vldD1)
        `DFF_INST(logic, startD1)
        always_comb begin
            n_sumLo   = element[0] + element[1] + element[2] + element[3];
            n_sumHi   = element[4] + element[5] + element[6] + element[7];
            n_vldD1   = inVld;
            n_startD1 = start;
            n_acc = acc;
            if (vldD1) begin
                n_acc = (startD1 ? '0 : acc) + sumLo + sumHi;
            end
        end
    end
endgenerate
```

## Generate blocks

### Conditional generation

```systemverilog
generate
    if (MODE == 1) begin : gen_mode1
        // Mode 1 logic
    end else if (MODE == 2) begin : gen_mode2
        // Mode 2 logic
    end
endgenerate
```

### Replicated logic

```systemverilog
genvar i;
generate
    for (i = 0; i < NUM_LANES; i++) begin : gen_lane
        `DFF_INST(laneT, laneData)
        assign n_laneData = laneIn[i];
        assign laneOut[i] = laneData;
    end
endgenerate
```

The generator writes memory and child instances from YAML, so never replicate those by hand.

Rules:
*   Always name generate blocks with `gen_<description>` labels.
*   Use `genvar` for generate loop variables.
*   Use `int` for `always_comb` / procedural loop variables.
*   A library instance on a non-default clock binds its clock and reset explicitly (`rtl-core.md`).

## FSM-sequenced memory reads (paired FSMs)

When multiple addresses must be read from `memory_if`, use an FSM to sequence them. The example uses the A2C Pro FSM macros. In a base project, write each FSM in the plain `case` form from `rtl-core.md`. `read_data` is valid one cycle after `enable`. Use two scoped FSMs in lockstep: one drives addresses, the other consumes `read_data` one cycle later:

```systemverilog
if (1) begin: gen_memReadFsm
    typedef enum logic [1:0] {RD0, RD1, RD2, RD3} statesT;
    `include "fsmDefs.svh"
    always_comb begin
        nState = state;
        mem.write_data = '0;
        mem.wr_en = 1'b0;
        mem.addr = addr0;
        mem.enable = 1'b0;

        `fsmCase
            `fsmState(RD0) begin
                if (trigger) begin
                    mem.enable = 1'b1;
                    `nxtState(RD1)
                end
            end
            `fsmState(RD1) begin
                mem.addr = addr1;
                mem.enable = 1'b1;
                `nxtState(RD2)
            end
            `fsmState(RD2) begin
                mem.addr = addr2;
                mem.enable = 1'b1;
                `nxtState(RD3)
            end
            `fsmState(RD3) begin
                mem.addr = addr3;
                mem.enable = 1'b1;
                `nxtState(RD0)
            end
            default: `qAssertFatal(0, "Default clause should not be reached")
        `fsmEndCase
    end
end: gen_memReadFsm

if (1) begin: gen_computeFsm
    typedef enum logic [1:0] {CALC0, CALC1, CALC2, CALC3} statesT;
    `include "fsmDefs.svh"
    always_comb begin
        nState = state;
        operand = '0;
        `fsmCase
            `fsmState(CALC0) begin
                operand = mem.read_data.val;  // data from RD0
                if (triggerD1) begin
                    `nxtState(CALC1)
                end
            end
            `fsmState(CALC1) begin
                operand = mem.read_data.val;  // data from RD1
                `nxtState(CALC2)
            end
            // ... CALC2, CALC3 follow same pattern
            default: `qAssertFatal(0, "Default clause should not be reached")
        `fsmEndCase
    end
end: gen_computeFsm
```

The same shape lets several multiplies share one registered multiplier, with an FSM that loads new operands into its inputs in each state.

See also `rtl-interfaces.md` for `memory_if` signal details.

## Related skills
*   FSMs, in the plain `case` form and with the A2C Pro `fsmDefs.svh` macros: `rtl-core.md`.
*   `rdy_vld` streaming stages and backpressure: `rtl-interfaces.md`.
*   `req_ack` requests: `rtl-interfaces.md`.
*   Several sources sharing one resource: `rtl-arbitration.md` (A2C Pro `memArb`, `vldAckArb`, `lockLocation`).
*   FIFOs and capture registers: `rtl-datapath.md` (A2C Pro `rdyVldFifo`, `rdyVldCapture`).
