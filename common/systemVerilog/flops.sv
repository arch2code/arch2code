// Flop macros
//
// Each family has exactly one body, defined by its _CLK variant, which takes the
// clock signal as its first argument. The bare macro is a one-line alias passing
// the literal `clk`, so a module whose clock port is named `clk` is unaffected
// and there is never a second definition of what a flop is that could diverge.
//
// The reset is deliberately NOT an argument: on the ASIC branch it comes from the
// overridable `RST, which is per compilation, so that branch cannot express two
// resets.

`ifndef FLOPS_SV
`define FLOPS_SV

`ifdef ASIC
// Flop definitions for ASIC flow, with sync reset

`ifndef RST
`define RST ~rstN
`endif

// D flop
`define DFF_CLK(clkSig, q, d) \
always_ff @(posedge clkSig) begin \
    q <= (`RST) ? '0 : (d); \
end

// D flop with initial value
`define DFFR_CLK(clkSig, q, d, rval) \
always_ff @(posedge clkSig) begin \
    q <= (`RST) ? rval : (d); \
end


// D flop explicitly with no reset value
`define DFFNR_CLK(clkSig, q, d) \
always_ff @(posedge clkSig) begin \
    q <= (d); \
end

// D flop with enable
`define DFFEN_CLK(clkSig, q, d, en) \
always_ff @(posedge clkSig) begin \
    q <= (`RST) ? '0 : ((en) ? (d) : q); \
end

// D flop with reset and enable
`define DFFREN_CLK(clkSig, q, d, en, rval) \
always_ff @(posedge clkSig) begin \
    q <= (`RST) ? rval : ((en) ? (d) : q); \
end

// Set clear flop, set priority
`define SCFF_CLK(clkSig, q, s, c) \
always_ff @(posedge clkSig) begin \
    q <= (`RST) ? '0 : ((q) & ~(c)) | (s); \
end

`else
// Flop definitions for FPGA flow, use initial statements
// to set start values in the FPGA image

// D flop
`define DFF_CLK(clkSig, q, d) \
initial q = '0; \
always_ff @(posedge clkSig) begin \
    q <= (d); \
end

// D flop with initial value
`define DFFR_CLK(clkSig, q, d, rval) \
initial q = rval; \
always_ff @(posedge clkSig) begin \
    q <= (d); \
end


// D flop explicitly with no reset value
`define DFFNR_CLK(clkSig, q, d) \
always_ff @(posedge clkSig) begin \
    q <= (d); \
end

// D flop with enable
`define DFFEN_CLK(clkSig, q, d, en) \
initial q = '0; \
always_ff @(posedge clkSig) begin \
    q <= (en) ? (d) : q; \
end

// D flop with reset and enable
`define DFFREN_CLK(clkSig, q, d, en, rval) \
initial q = rval; \
always_ff @(posedge clkSig) begin \
    q <= (en) ? (d) : q; \
end

// Set clear flop, set priority
`define SCFF_CLK(clkSig, q, s, c) \
initial q = '0; \
always_ff @(posedge clkSig) begin \
    q <= ((q) & ~(c)) | (s); \
end

`endif // ASIC


// Single-domain aliases, clocked by the port named clk. Each is one line so that
// a bare macro and its _CLK variant can never describe different hardware. They
// are outside the branches above because both branches define the same _CLK
// signatures.
`define DFF(q, d)               `DFF_CLK(clk, q, d)
`define DFFR(q, d, rval)        `DFFR_CLK(clk, q, d, rval)
`define DFFNR(q, d)             `DFFNR_CLK(clk, q, d)
`define DFFEN(q, d, en)         `DFFEN_CLK(clk, q, d, en)
`define DFFREN(q, d, en, rval)  `DFFREN_CLK(clk, q, d, en, rval)
`define SCFF(q, s, c)           `SCFF_CLK(clk, q, s, c)


// Defines to instantate the flops given a signal type and name
`define DFF_INST_CLK(clkSig, type, name) \
type name, n_``name; \
`DFF_CLK(clkSig, name, n_``name)

`define DFFR_INST_CLK(clkSig, type, name, rval) \
type name, n_``name; \
`DFFR_CLK(clkSig, name, n_``name, rval)

`define DFFNR_INST_CLK(clkSig, type, name) \
type name, n_``name; \
`DFFNR_CLK(clkSig, name, n_``name)

`define DFFEN_INST_CLK(clkSig, type, name, en) \
type name, n_``name; \
`DFFEN_CLK(clkSig, name, n_``name, en)

`define DFF_INST(type, name)            `DFF_INST_CLK(clk, type, name)
`define DFFR_INST(type, name, rval)     `DFFR_INST_CLK(clk, type, name, rval)
`define DFFNR_INST(type, name)          `DFFNR_INST_CLK(clk, type, name)
`define DFFEN_INST(type, name, en)      `DFFEN_INST_CLK(clk, type, name, en)

`endif  // FLOPS_SV
