---
name: rtl-patterns
description: Reference for common RTL implementation patterns including pipelines, FSMs, interpolation, saturation, resource sharing, and memory access sequences
globs: "rtl/**/*.sv, rtl/**/*.svh"
alwaysApply: false
---
# Skill: RTL Patterns

## Purpose
Reference common RTL implementation patterns to solve frequent design problems efficiently and consistently in SystemVerilog.

## 1. Pipeline Stage Pattern

Pipelines are the most common structure. Each stage propagates `vld`, `data`, and sideband metadata (e.g., transaction IDs, frame signals, sequence numbers):

```systemverilog
// Stage 1: Capture input
`DFF_INST(data_t, s1_data)
`DFF_INST(meta_t, s1_meta)
`DFF_INST(logic, s1_vld)

always_comb begin
    n_s1_vld  = in_port.vld;
    n_s1_meta = in_port.data.meta;
    n_s1_data = in_port.data.payload;
end

// Stage 2: Process
`DFF_INST(logic, s2_vld)
`DFF_INST(meta_t, s2_meta)
`DFF_INST(result_t, s2_result)

always_comb begin
    n_s2_vld    = s1_vld;
    n_s2_meta   = s1_meta;
    n_s2_result = s1_data * coeff;
end

// Stage 3: Output
`DFF_INST(out_data_t, s3_data)
`DFF_INST(meta_t, s3_meta)
`DFF_INST(logic, s3_vld)

always_comb begin
    n_s3_vld  = s2_vld;
    n_s3_meta = s2_meta;
    n_s3_data = clip(s2_result);
end

// Drive output
assign out_port.vld       = s3_vld;
assign out_port.data.payload = s3_data;
assign out_port.data.meta    = s3_meta;
```

**Key rules:**
*   Propagate `vld` and all sideband signals through every stage.
*   Use `assign` from last stage or `always_comb` when driving multiple interfaces.

## 2. Hold-Value-Else Pattern

When pipeline data must be held on invalid cycles, use an explicit `if/else` with the else branch re-assigning current values:

```systemverilog
always_comb begin
    n_stg2_vld = stg1_vld;
    if (stg1_vld) begin
        n_stg2_data = stg1_data;
        n_stg2_meta = stg1_meta;
    end else begin
        n_stg2_data = stg2_data;    // hold current value
        n_stg2_meta = stg2_meta;    // hold current value
    end
end
```

Alternative to the "default-at-top" style. Use when hold behavior must be explicit for all signals.

## 3. Finite State Machine (FSM)
Use for control logic with multiple states.
*   **Key:** Use `always_comb` for next state logic and DFF macros for state register.
*   **Ref:** `rtl-core.md`

## 4. Streaming Pipeline (`rdy_vld`)
Use for data processing stages.
*   **Forward Flow:** `vld` indicates data availability.
*   **Backward Flow:** `rdy` indicates ability to accept.
*   **Logic:** `process_en = in.vld & out.rdy`.
*   **Ref:** `rtl-interfaces.md`

## 5. Request-Response (`req_ack`)
Use for transactional operations (e.g., memory access, configuration).
*   **Req:** Source drives `req` high.
*   **Ack:** Destination drives `ack` high when complete.
*   **Handshake:** Source holds `req` until `ack` is seen.

## 6. Arbitration
Use when multiple sources contend for a single resource.
*   **Round Robin:** Fair access.
*   **Fixed Priority:** Critical path optimization.
*   **Components:** `memArb` (memory ports), `vldAckArb` (streaming interfaces).
*   **Ref:** `rtl-arbitration.md`

## 7. Datapath Buffering
Use to break timing paths or match rates.
*   **FIFO:** Store data, decouple rates.
*   **Capture Reg:** Latch `rdy_vld` data (`rdyVldCapture`).
*   **Ref:** `rtl-datapath.md`

## 8. Position / Counter Tracking Pattern

Track position within a stream using start/end boundary signals. Common in streaming datapaths where you need to know row/column index, element position, or group boundaries.

Use a delayed end-of-group signal as start-of-next-group. Extract sub-indices via bit-slicing (zero-cost division/modulo):

```systemverilog
`DFF_INST(x_pos_t, pos_x)
`DFF_INST(y_pos_t, pos_y)
`DFF_INST(logic, start_of_group)

always_comb begin
    n_pos_x = pos_x;
    n_pos_y = pos_y;
    n_start_of_group = in_meta.end_of_group;

    if (in_vld) begin
        if (in_meta.start_of_frame) begin
            n_pos_x = '0;
            n_pos_y = '0;
        end else if (start_of_group) begin
            n_pos_x = '0;
            n_pos_y = pos_y + 1;
        end else begin
            n_pos_x = pos_x + x_pos_t'(ELEMENTS_PER_CYCLE);
        end
    end
end

// Bit-slicing for grid index and sub-grid offset (zero-cost in hardware)
grid_idx_t grid_y;
grid_count_t sub_y;
always_comb begin
    grid_y = pos_y[MSB:GRID_SIZE_LOG2];               // pos_y / GRID_SIZE
    sub_y  = {1'b0, pos_y[GRID_SIZE_LOG2-1:0]};       // pos_y % GRID_SIZE
end
```

## 9. Piecewise-Linear Interpolation (Slope-Accumulate)

For linear interpolation across a grid or region, compute the start value and slope at the boundary, then accumulate per-cycle:

```systemverilog
`DFF_INST(factor_t, interp_val)
`DFF_INST(factor_t, interp_slope)

always_comb begin
    if (boundary_start) begin
        n_interp_val   = start_value;
        n_interp_slope = (end_value - start_value) >>> DIVISIONS_LOG2;
    end else begin
        n_interp_val   = interp_val + interp_slope;  // accumulate
        n_interp_slope = interp_slope;                // hold slope
    end
end
```

Use `>>>` (arithmetic shift right) for signed values to preserve the sign bit. Use `>>` only for unsigned values.

## 10. Saturation / Clipping Patterns

Three common patterns:

**Signed two-sided clamp** (negative -> 0, overflow -> max, else extract):
```systemverilog
function automatic result_t saturate(input accum_t accum);
    if (accum[ACCUM_W-1]) return result_t'('0);
    if (|accum[ACCUM_W-2:RESULT_WIDTH]) return result_t'(2**RESULT_WIDTH-1);
    return result_t'(accum);
endfunction
```

**Unsigned fixed-point overflow clip** (MSB check on multiply result):
```systemverilog
function automatic result_t clip_mult(input mult_out_t mult_val);
    if (|mult_val[WIDTH-1:WIDTH-INTEGER_WIDTH]) return result_t'(MAX_VALUE);
    return result_t'(mult_val[WIDTH-1-INTEGER_WIDTH:WIDTH-INTEGER_WIDTH-RESULT_WIDTH]);
endfunction
```

**Unsigned subtraction with floor-clamp** (prevent underflow):
```systemverilog
n_out_val = (in_val > offset) ? (in_val - offset) : result_t'('0);
```

## 11. Rounding Functions

Hardware-friendly banker's rounding (round half to even) for power-of-2 divisors:

```systemverilog
localparam W_P1 = WIDTH + 1;
localparam W_P2 = WIDTH + 2;
typedef logic [W_P1-1:0] acc2_t;
typedef logic [W_P2-1:0] acc4_t;

function automatic result_t round_div2(input acc2_t sum);
    return (sum[1:0] == 2'b11) ? (sum[W_P1-1:1] + 1'b1) : sum[W_P1-1:1];
endfunction

function automatic result_t round_div4(input acc4_t sum);
    return ((sum[1:0] == 2'b11) || (sum[1:0] == 2'b10 && sum[2] == 1'b1)) ?
        (sum[W_P2-1:2] + 1'b1) : sum[W_P2-1:2];
endfunction
```

## 12. Shared Multiplier (Resource Reuse via FSM)

When a complex calculation requires multiple multiplications, use a single shared multiplier driven by an FSM that loads different operands each cycle. Maps to a single DSP block in FPGA:

```systemverilog
`DFF_INST(mult_in_t, mult_in_a)
`DFF_INST(mult_in_t, mult_in_b)
`DFF_INST(mult_out_t, mult_out)
always_comb begin
    n_mult_out = mult_in_a * mult_in_b;
end
// FSM loads different operands into mult_in_a/b each state
```

## 13. Parallel-Lane Reduction Trees

When accumulating across `LANES` parallel elements, use `generate if` for lane-count-specific partial sum trees. Higher lane counts need intermediate pipeline stages:

```systemverilog
generate
    if (LANES == 1) begin : gen_1lane
        always_comb n_acc = in_vld ? (start ? element[0] : acc + element[0]) : acc;
    end else if (LANES == 4) begin : gen_4lane
        always_comb n_acc = in_vld ? (start ? (element[0] + element[1] + element[2] + element[3])
                                            : acc + element[0] + element[1] + element[2] + element[3])
                                   : acc;
    end else if (LANES == 8) begin : gen_8lane
        `DFF_INST(partial_t, partial_sum)
        always_comb n_partial_sum = element[0] + element[1] + element[2] + element[3];
        always_comb n_acc = vld_d1 ? (start_d1 ? partial_sum
                                               : acc + partial_sum + element[4] + element[5] + element[6] + element[7])
                                   : acc;
    end
endgenerate
```

## 14. Generate Blocks

### Conditional Generation

```systemverilog
generate
    if (MODE == 1) begin : gen_mode1
        // Mode 1 logic
    end else if (MODE == 2) begin : gen_mode2
        // Mode 2 logic
    end
endgenerate
```

### Replicated Instances

```systemverilog
genvar i;
generate
    for (i = 0; i < NUM_PORTS; i++) begin : gen_mem_inst
        memory_dp #(.DEPTH(MEM_DEPTH), .data_t(mem_data_t)) mem_inst (
            .mem_portA (mem_rd[i]),
            .mem_portB (mem_wr[i]),
            .clk (clk)
        );
    end
endgenerate
```

**Rules:**
*   Always name generate blocks with `gen_<description>` labels.
*   Use `genvar` for generate loop variables.
*   Use `int` for `always_comb` / procedural loop variables.

## 15. FSM-Sequenced Memory Reads (Paired FSMs)

When multiple addresses must be read from `memory_if`, use an FSM to sequence them. `read_data` is valid one cycle after `enable`. Use two scoped FSMs in lockstep: one drives addresses, the other consumes `read_data` one cycle later:

```systemverilog
if (1) begin: mem_read_fsm
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
        `fsmEndCase
    end
end: mem_read_fsm

if (1) begin: compute_fsm
    typedef enum logic [1:0] {CALC0, CALC1, CALC2, CALC3} statesT;
    `include "fsmDefs.svh"
    always_comb begin
        nState = state;
        `fsmCase
            `fsmState(CALC0) begin
                operand = mem.read_data.val;  // data from RD0
                if (trigger_d1) `nxtState(CALC1)
            end
            `fsmState(CALC1) begin
                operand = mem.read_data.val;  // data from RD1
                `nxtState(CALC2)
            end
            // ... CALC2, CALC3 follow same pattern
        `fsmEndCase
    end
end: compute_fsm
```

See also `rtl-interfaces.md` for `memory_if` signal details.
