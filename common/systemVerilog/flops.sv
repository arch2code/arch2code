// Flop macros

`ifndef FLOPS_SV
`define FLOPS_SV

`ifdef ASIC
// Flop definitions for ASIC flow, with sync reset
// D flop
`define RST ~rstN
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
initial q = '0; \
always_ff @(posedge clk) begin \
    q <= (`RST) ? '0 : ((en) ? (d) : q); \
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

// Set clear flop, set priority
`define SCFF(q, s, c) \
initial q = '0; \
always_ff @(posedge clk) begin \
    q <= ((q) & ~(c)) | (s); \
end

`endif // ASIC

`endif  // FLOPS_SV