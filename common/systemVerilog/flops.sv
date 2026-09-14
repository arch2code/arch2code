// Flop macros
//
// Each family has exactly one body per reset style, defined by its _DOM
// variant, which takes the clock signal and the reset signal as its first two
// arguments. _CLK supplies `rst_n` for that reset, which every block module
// has as a port or as the generated default-domain alias; bare supplies
// `clk`. Each alias is one line, so a family and its aliases can never
// describe different hardware.
//
// Exactly one of three reset styles is active, selected below:
//   A2C_RESET_SYNC  - synchronous, active-low reset applied in the clocked
//                     always_ff. This is the default when nothing is defined.
//   A2C_RESET_ASYNC - asynchronous, active-low reset on the flop's own
//                     posedge-clock/negedge-reset sensitivity list.
//   A2C_RESET_NONE  - no reset; an `initial` statement sets the start value
//                     for FPGA image flows instead.
// `ASIC` aliases to A2C_RESET_SYNC and `FPGA_INIT_FLOPS` aliases to
// A2C_RESET_NONE for compatibility with existing defines. Defining more than
// one style is a compile error (see below).

`ifndef FLOPS_SV
`define FLOPS_SV

// Each alias is guarded so naming a style both ways is not a define override.
`ifdef ASIC
`ifndef A2C_RESET_SYNC
`define A2C_RESET_SYNC
`endif
`endif

`ifdef FPGA_INIT_FLOPS
`ifndef A2C_RESET_NONE
`define A2C_RESET_NONE
`endif
`endif

`ifndef A2C_RESET_SYNC
`ifndef A2C_RESET_ASYNC
`ifndef A2C_RESET_NONE
`define A2C_RESET_SYNC
`endif
`endif
`endif

// Fails to compile if more than one reset style is selected: each branch
// below references a macro that is never defined, so the preprocessor errors
// on the undefined reference instead of silently picking one style.
`ifdef A2C_RESET_SYNC
`ifdef A2C_RESET_ASYNC
`A2C_RESET_STYLE_CONFLICT_SYNC_ASYNC
`endif
`ifdef A2C_RESET_NONE
`A2C_RESET_STYLE_CONFLICT_SYNC_NONE
`endif
`endif
`ifdef A2C_RESET_ASYNC
`ifdef A2C_RESET_NONE
`A2C_RESET_STYLE_CONFLICT_ASYNC_NONE
`endif
`endif

`ifdef A2C_RESET_SYNC
// Synchronous, active-low reset applied in the clocked always_ff.

// D flop
`define DFF_DOM(clkSig, rstSig, q, d) \
always_ff @(posedge clkSig) begin \
    q <= (~rstSig) ? '0 : (d); \
end

// D flop with initial value
`define DFFR_DOM(clkSig, rstSig, q, d, rval) \
always_ff @(posedge clkSig) begin \
    q <= (~rstSig) ? rval : (d); \
end

// D flop explicitly with no reset value
`define DFFNR_DOM(clkSig, rstSig, q, d) \
always_ff @(posedge clkSig) begin \
    q <= (d); \
end

// D flop with enable
`define DFFEN_DOM(clkSig, rstSig, q, d, en) \
always_ff @(posedge clkSig) begin \
    q <= (~rstSig) ? '0 : ((en) ? (d) : q); \
end

// D flop with reset and enable
`define DFFREN_DOM(clkSig, rstSig, q, d, en, rval) \
always_ff @(posedge clkSig) begin \
    q <= (~rstSig) ? rval : ((en) ? (d) : q); \
end

// Set clear flop, set priority
`define SCFF_DOM(clkSig, rstSig, q, s, c) \
always_ff @(posedge clkSig) begin \
    q <= (~rstSig) ? '0 : ((q) & ~(c)) | (s); \
end

`elsif A2C_RESET_ASYNC
// Asynchronous, active-low reset on the flop's own sensitivity list.

// D flop
`define DFF_DOM(clkSig, rstSig, q, d) \
always_ff @(posedge clkSig or negedge rstSig) begin \
    if (~rstSig) q <= '0; \
    else q <= (d); \
end

// D flop with initial value
`define DFFR_DOM(clkSig, rstSig, q, d, rval) \
always_ff @(posedge clkSig or negedge rstSig) begin \
    if (~rstSig) q <= rval; \
    else q <= (d); \
end

// D flop explicitly with no reset value
`define DFFNR_DOM(clkSig, rstSig, q, d) \
always_ff @(posedge clkSig) begin \
    q <= (d); \
end

// D flop with enable
`define DFFEN_DOM(clkSig, rstSig, q, d, en) \
always_ff @(posedge clkSig or negedge rstSig) begin \
    if (~rstSig) q <= '0; \
    else if (en) q <= (d); \
end

// D flop with reset and enable
`define DFFREN_DOM(clkSig, rstSig, q, d, en, rval) \
always_ff @(posedge clkSig or negedge rstSig) begin \
    if (~rstSig) q <= rval; \
    else if (en) q <= (d); \
end

// Set clear flop, set priority
`define SCFF_DOM(clkSig, rstSig, q, s, c) \
always_ff @(posedge clkSig or negedge rstSig) begin \
    if (~rstSig) q <= '0; \
    else q <= ((q) & ~(c)) | (s); \
end

`elsif A2C_RESET_NONE
// No reset: use initial statements to set start values in the FPGA image.

// D flop
`define DFF_DOM(clkSig, rstSig, q, d) \
initial q = '0; \
always_ff @(posedge clkSig) begin \
    q <= (d); \
end

// D flop with initial value
`define DFFR_DOM(clkSig, rstSig, q, d, rval) \
initial q = rval; \
always_ff @(posedge clkSig) begin \
    q <= (d); \
end

// D flop explicitly with no reset value
`define DFFNR_DOM(clkSig, rstSig, q, d) \
always_ff @(posedge clkSig) begin \
    q <= (d); \
end

// D flop with enable
`define DFFEN_DOM(clkSig, rstSig, q, d, en) \
initial q = '0; \
always_ff @(posedge clkSig) begin \
    q <= (en) ? (d) : q; \
end

// D flop with reset and enable
`define DFFREN_DOM(clkSig, rstSig, q, d, en, rval) \
initial q = rval; \
always_ff @(posedge clkSig) begin \
    q <= (en) ? (d) : q; \
end

// Set clear flop, set priority
`define SCFF_DOM(clkSig, rstSig, q, s, c) \
initial q = '0; \
always_ff @(posedge clkSig) begin \
    q <= ((q) & ~(c)) | (s); \
end

`endif


// Single-domain aliases, reset by the port named rst_n. Each is one line so
// that a _CLK variant and its _DOM body can never describe different
// hardware. Outside the branches above because all three define the same
// _DOM signatures.
`define DFF_CLK(clkSig, q, d)               `DFF_DOM(clkSig, rst_n, q, d)
`define DFFR_CLK(clkSig, q, d, rval)        `DFFR_DOM(clkSig, rst_n, q, d, rval)
`define DFFNR_CLK(clkSig, q, d)             `DFFNR_DOM(clkSig, rst_n, q, d)
`define DFFEN_CLK(clkSig, q, d, en)         `DFFEN_DOM(clkSig, rst_n, q, d, en)
`define DFFREN_CLK(clkSig, q, d, en, rval)  `DFFREN_DOM(clkSig, rst_n, q, d, en, rval)
`define SCFF_CLK(clkSig, q, s, c)           `SCFF_DOM(clkSig, rst_n, q, s, c)

// Single-domain aliases, clocked by the port named clk.
`define DFF(q, d)               `DFF_CLK(clk, q, d)
`define DFFR(q, d, rval)        `DFFR_CLK(clk, q, d, rval)
`define DFFNR(q, d)             `DFFNR_CLK(clk, q, d)
`define DFFEN(q, d, en)         `DFFEN_CLK(clk, q, d, en)
`define DFFREN(q, d, en, rval)  `DFFREN_CLK(clk, q, d, en, rval)
`define SCFF(q, s, c)           `SCFF_CLK(clk, q, s, c)


// Defines to instantiate the flops given a signal type and name
`define DFF_INST_DOM(clkSig, rstSig, type, name) \
type name, n_``name; \
`DFF_DOM(clkSig, rstSig, name, n_``name)

`define DFFR_INST_DOM(clkSig, rstSig, type, name, rval) \
type name, n_``name; \
`DFFR_DOM(clkSig, rstSig, name, n_``name, rval)

`define DFFNR_INST_DOM(clkSig, rstSig, type, name) \
type name, n_``name; \
`DFFNR_DOM(clkSig, rstSig, name, n_``name)

`define DFFEN_INST_DOM(clkSig, rstSig, type, name, en) \
type name, n_``name; \
`DFFEN_DOM(clkSig, rstSig, name, n_``name, en)

`define DFF_INST_CLK(clkSig, type, name)              `DFF_INST_DOM(clkSig, rst_n, type, name)
`define DFFR_INST_CLK(clkSig, type, name, rval)       `DFFR_INST_DOM(clkSig, rst_n, type, name, rval)
`define DFFNR_INST_CLK(clkSig, type, name)            `DFFNR_INST_DOM(clkSig, rst_n, type, name)
`define DFFEN_INST_CLK(clkSig, type, name, en)        `DFFEN_INST_DOM(clkSig, rst_n, type, name, en)

`define DFF_INST(type, name)            `DFF_INST_CLK(clk, type, name)
`define DFFR_INST(type, name, rval)     `DFFR_INST_CLK(clk, type, name, rval)
`define DFFNR_INST(type, name)          `DFFNR_INST_CLK(clk, type, name)
`define DFFEN_INST(type, name, en)      `DFFEN_INST_CLK(clk, type, name, en)

// Same as DFF_INST but marks the register as keep/preserve so Synplify does not
// share/merge it with an apparently-equivalent register.
`define DFF_KEEP_INST_DOM(clkSig, rstSig, type, name) \
(* syn_keep = "true", syn_preserve = "true" *) type name; \
type n_``name; \
`DFF_DOM(clkSig, rstSig, name, n_``name)

`define DFF_KEEP_INST_CLK(clkSig, type, name)  `DFF_KEEP_INST_DOM(clkSig, rst_n, type, name)
`define DFF_KEEP_INST(type, name)              `DFF_KEEP_INST_CLK(clk, type, name)

`endif  // FLOPS_SV
