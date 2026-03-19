# SystemVerilog RTL Rules

These rules apply to files in `rtl/` directory.

## Generated Code Protection

### Never Edit
- Code between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END` markers
- These sections are regenerated when you run `make gen`

## Coding Standards

### Use `logic` Over `reg`/`wire`
```systemverilog
// GOOD
logic [31:0] data;
logic        valid;

// AVOID
reg [31:0] data;
wire       valid;
```

### Sequential Logic: `always_ff`
```systemverilog
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
        counter <= '0;
    end else begin
        state <= next_state;
        counter <= counter + 1;
    end
end
```

### Combinational Logic: `always_comb`
```systemverilog
always_comb begin
    next_state = state;
    output_valid = 1'b0;
    
    case (state)
        IDLE: begin
            if (start) next_state = ACTIVE;
        end
        ACTIVE: begin
            output_valid = 1'b1;
            if (done) next_state = IDLE;
        end
    endcase
end
```

## Package Imports

Import generated packages at module declaration:
```systemverilog
module my_module
    import my_module_package::*;
    import shared_types_package::*;
(
    input  logic clk,
    input  logic rst_n,
    // ports...
);
```

## Module Structure

```systemverilog
module my_module
    import my_module_package::*;
(
    input  logic clk,
    input  logic rst_n,
    // Interface ports
    rdy_vld_if.dst  data_in,
    rdy_vld_if.src  data_out
);

// GENERATED_CODE_BEGIN --template=registers
// ... generated register logic ...
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=instances  
// ... generated sub-module instances ...
// GENERATED_CODE_END

logic [31:0] processed_data;

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        processed_data <= '0;
    end else if (data_in.vld && data_in.rdy) begin
        processed_data <= transform(data_in.data);
    end
end

endmodule
```

## Interface Usage

### Ready/Valid Sink (Receiving)
```systemverilog
// Accept data when ready
assign data_in.rdy = can_accept;

always_ff @(posedge clk) begin
    if (data_in.vld && data_in.rdy) begin
        captured_data <= data_in.data;
    end
end
```

### Ready/Valid Source (Sending)
```systemverilog
assign data_out.vld = have_data;
assign data_out.data = output_data;

// Data transfers when both vld and rdy
wire transfer = data_out.vld && data_out.rdy;
```

## Linting

Run lint checks from the `rtl/` directory:
```bash
cd rtl
make lint
```

Fix all lint errors before committing.

## Best Practices

1. **Use generated types** - Don't redefine structures manually
2. **Keep implementation in designated sections** - Preserves regeneration
3. **Use non-blocking assignments** (`<=`) in sequential blocks
4. **Use blocking assignments** (`=`) in combinational blocks
5. **Reset all sequential elements** - Explicit reset values
6. **Lint before commit** - `make lint` catches common issues

## FSM Macros (`fsmDefs.svh`)

Do NOT write raw `case` statements for state machines. Use `fsmDefs.svh` macros:

```systemverilog
typedef enum logic [1:0] {RDY, WORK, DONE} statesT;
`include "fsmDefs.svh"

always_comb begin
    nState = state;
    out_vld = 1'b0;

    `fsmCase
        `fsmState(RDY) begin
            if (start) `nxtState(WORK)
        end
        `fsmState(WORK) begin
            out_vld = 1'b1;
            if (out_ack) `nxtState(DONE)
        end
        `fsmState(DONE) begin
            `nxtState(RDY)
        end
        default: `qAssertFatal(0, "Default clause should not be reached")
    `fsmEndCase
end
```

## Flip-Flop Macros

Use macros instead of explicit `always_ff` blocks for standard registers:

- `` `DFF(q, d) `` -- Standard register (no reset)
- `` `DFFR(q, d, RESET_VAL) `` -- Register with reset value

```systemverilog
`DFF(data_q, data_d)
`DFFR(counter_q, counter_d, '0)
```

Only write explicit `always_ff` for complex reset logic not covered by macros.

## Assertions

Use `qAssert` / `qAssertFatal` for runtime checks:

```systemverilog
`qAssert(index < MAX_SIZE, "Index out of range")
`qAssertFatal(state != ILLEGAL, "Illegal state reached")
```

`qAssertFatal` halts simulation immediately; `qAssert` logs an error but continues.

## Common Patterns

### Pipeline Stage
```systemverilog
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        stage_valid <= 1'b0;
        stage_data <= '0;
    end else if (input_valid && input_ready) begin
        stage_valid <= 1'b1;
        stage_data <= input_data;
    end else if (output_ready) begin
        stage_valid <= 1'b0;
    end
end
```

### FIFO Control
```systemverilog
assign full = (wr_ptr == rd_ptr) && ptr_wrap_diff;
assign empty = (wr_ptr == rd_ptr) && !ptr_wrap_diff;
assign push = wr_en && !full;
assign pop = rd_en && !empty;
```
