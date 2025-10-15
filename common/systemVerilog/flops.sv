// Flop macros

`ifndef FLOPS_SV
`define FLOPS_SV

`ifdef ASIC
// Flop definitions for ASIC flow, with sync reset

`ifndef RST
`define RST ~rstN
`endif

// D flop
`define DFF(q, d) \
always_ff @(posedge clk) begin \
    q <= (`RST) ? '0 : (d); \
end

// D flop with initial value
`define DFFR(q, d, rval) \
always_ff @(posedge clk) begin \
    q <= (`RST) ? rval : (d); \
end


// D flop explicitly with no reset value
`define DFFNR(q, d) \
always_ff @(posedge clk) begin \
    q <= (d); \
end

// D flop with enable
`define DFFEN(q, d, en) \
always_ff @(posedge clk) begin \
    q <= (`RST) ? '0 : ((en) ? (d) : q); \
end

// D flop with reset and enable
`define DFFREN(q, d, en, rval) \
always_ff @(posedge clk) begin \
    q <= (`RST) ? rval : ((en) ? (d) : q); \
end

// Set clear flop, set priority
`define SCFF(q, s, c) \
always_ff @(posedge clk) begin \
    q <= (`RST) ? '0 : ((q) & ~(c)) | (s); \
end

`else
// Flop definitions for FPGA flow, use initial statements
// to set start values in the FPGA image

// D flop
`define DFF(q, d) \
initial q = '0; \
always_ff @(posedge clk) begin \
    q <= (d); \
end

// D flop with initial value
`define DFFR(q, d, rval) \
initial q = rval; \
always_ff @(posedge clk) begin \
    q <= (d); \
end


// D flop explicitly with no reset value
`define DFFNR(q, d) \
always_ff @(posedge clk) begin \
    q <= (d); \
end

// D flop with enable
`define DFFEN(q, d, en) \
initial q = '0; \
always_ff @(posedge clk) begin \
    q <= (en) ? (d) : q; \
end

// D flop with reset and enable
`define DFFREN(q, d, en, rval) \
initial q = rval; \
always_ff @(posedge clk) begin \
    q <= (en) ? (d) : q; \
end

// Set clear flop, set priority
`define SCFF(q, s, c) \
initial q = '0; \
always_ff @(posedge clk) begin \
    q <= ((q) & ~(c)) | (s); \
end

`endif // ASIC


// Defines to instantate the flops given a signal type and name
`define DFF_INST(type, name) \
type name, n_``name; \
`DFF(name, n_``name)

`define DFFR_INST(type, name, rval) \
type name, n_``name; \
`DFFR(name, n_``name, rval)

`define DFFNR_INST(type, name) \
type name, n_``name; \
`DFFNR(name, n_``name)

`define DFFEN_INST(type, name, en) \
type name, n_``name; \
`DFFEN(name, n_``name, en)

`endif  // FLOPS_SV