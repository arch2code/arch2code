`timescale 1ns/1ps

// Four-state cases for the <type>_xcheck module of each type in TYPES of
// run_xcheck_test.sh, which builds this and runs it. Each case module drives
// one interface into one checker with its own reset, and xz_count.c counts the
// checker's reports, so every case expects an exact count and first signal.
//
// Signals change just after a rising edge and the checkers sample on the
// falling edge, so an X held for one cycle is sampled exactly once.

module rv_case #(parameter int CASE = 0, parameter int EXP = 0,
                 parameter string SIG = "", parameter string NAME = "") (input logic clk);
    typedef struct packed {
        logic [3:0] hi;
        logic [3:0] lo;
    } data_t;
    logic rst_n;
    rdy_vld_if #(.data_t(data_t)) intf();
    rdy_vld_xcheck u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    localparam string CHK = "u_chk";
`include "xcheck_case.svh"

    task automatic idle();
        intf.vld = 1'b0;
        intf.rdy = 1'b1;
        intf.data = '0;
    endtask

    task automatic all_x();
        intf.vld = 1'bx;
        intf.rdy = 1'bx;
        intf.data = 'x;
    endtask

    initial begin
        case (CASE)
            0: begin // data X while vld is high, twice
                rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
                intf.vld = 1'b1; intf.data = 'x; cycles(1); idle(); cycles(2);
                intf.vld = 1'b1; intf.data = 'x; cycles(1); idle();
            end
            1: begin // data X while vld is low
                rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
                intf.data = 'x; cycles(3); idle();
            end
            2: begin
                rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
                intf.vld = 1'bx; cycles(1); idle();
            end
            3: begin
                rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
                intf.rdy = 1'bx; cycles(1); idle();
            end
            4: begin // X before the first reset, during it, and during a later one
                rst_n = 1'b1; all_x(); cycles(3);
                rst_n = 1'b0; cycles(2);
                idle(); rst_n = 1'b1; cycles(3);
                rst_n = 1'b0; all_x(); cycles(3);
                idle(); rst_n = 1'b1; cycles(3);
            end
            5: begin // reset X from power-on, then released without being low
                rst_n = 1'bx; all_x(); cycles(3);
                rst_n = 1'b1; cycles(3); idle();
            end
            6: begin // reset released before the first clock edge
                idle(); delta_reset(); cycles(3);
                intf.vld = 1'bx; cycles(1); idle();
            end
        endcase
    end
endmodule

module apb_case #(parameter int CASE = 0, parameter int EXP = 0,
                  parameter string SIG = "", parameter string NAME = "") (input logic clk);
    logic rst_n;
    apb_if #(.addr_t(logic [31:0]), .data_t(logic [31:0])) intf();
    apb_xcheck u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    localparam string CHK = "u_chk";
`include "xcheck_case.svh"

    task automatic idle();
        intf.paddr = '0;
        intf.psel = 1'b0;
        intf.penable = 1'b0;
        intf.pwrite = 1'b0;
        intf.pwdata = '0;
        intf.pready = 1'b0;
        intf.prdata = '0;
        intf.pslverr = 1'b0;
    endtask

    task automatic all_x();
        intf.paddr = 'x;
        intf.psel = 1'bx;
        intf.penable = 1'bx;
        intf.pwrite = 1'bx;
        intf.pwdata = 'x;
        intf.pready = 1'bx;
        intf.prdata = 'x;
        intf.pslverr = 1'bx;
    endtask

    // The completing cycle of a transfer, psel && penable && pready.
    task automatic complete(logic write);
        intf.psel = 1'b1;
        intf.penable = 1'b1;
        intf.pready = 1'b1;
        intf.pwrite = write;
    endtask

    task automatic armed();
        rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
    endtask

    initial begin
        case (CASE)
            0: begin armed(); intf.psel = 1'bx; cycles(1); idle(); end
            1: begin armed(); intf.penable = 1'bx; cycles(1); idle(); end
            2: begin armed(); intf.pready = 1'bx; cycles(1); idle(); end
            3: begin armed(); intf.psel = 1'b1; intf.paddr = 'x; cycles(1); idle(); end
            4: begin armed(); intf.paddr = 'x; cycles(3); idle(); end
            5: begin armed(); intf.psel = 1'b1; intf.pwrite = 1'bx; cycles(1); idle(); end
            6: begin // pwdata X on a write, twice
                armed();
                intf.psel = 1'b1; intf.pwrite = 1'b1; intf.pwdata = 'x; cycles(1); idle(); cycles(2);
                intf.psel = 1'b1; intf.pwrite = 1'b1; intf.pwdata = 'x; cycles(1); idle();
            end
            7: begin armed(); intf.psel = 1'b1; intf.pwdata = 'x; cycles(3); idle(); end
            8: begin armed(); complete(1'b0); intf.pslverr = 1'bx; cycles(1); idle(); end
            9: begin // pslverr X while the slave still waits
                armed(); complete(1'b0); intf.pready = 1'b0; intf.pslverr = 1'bx; cycles(3); idle();
            end
            10: begin armed(); complete(1'b0); intf.prdata = 'x; cycles(1); idle(); end
            11: begin armed(); complete(1'b1); intf.prdata = 'x; cycles(3); idle(); end
            12: begin // prdata X on a read the slave has not completed
                armed(); complete(1'b0); intf.pready = 1'b0; intf.prdata = 'x; cycles(3); idle();
            end
            13: begin
                rst_n = 1'b1; all_x(); cycles(3);
                rst_n = 1'b0; cycles(2);
                idle(); rst_n = 1'b1; cycles(3);
                rst_n = 1'b0; all_x(); cycles(3);
                idle(); rst_n = 1'b1; cycles(3);
            end
            14: begin
                rst_n = 1'bx; all_x(); cycles(3);
                rst_n = 1'b1; cycles(3); idle();
            end
            15: begin idle(); delta_reset(); cycles(3); intf.psel = 1'bx; cycles(1); idle(); end
        endcase
    end
endmodule

// TUSER_BOUND picks whether the stream binds a TUSER type, and is passed to
// the checker as the wrapper passes it.
module axis_case #(parameter int CASE = 0, parameter int EXP = 0,
                   parameter string SIG = "", parameter string NAME = "",
                   parameter bit TUSER_BOUND = 1'b1) (input logic clk);
    logic rst_n;
    if (TUSER_BOUND) begin : g_if
        axi4_stream_if #(.tdata_t(logic [15:0]), .tid_t(logic [1:0]), .tdest_t(logic [2:0]),
                         .tuser_t(logic [1:0])) intf();
        axi4_stream_xcheck #(.CHECK_TUSER(1'b1)) u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    end else begin : g_if
        axi4_stream_if #(.tdata_t(logic [15:0]), .tid_t(logic [1:0]), .tdest_t(logic [2:0])) intf();
        axi4_stream_xcheck #(.CHECK_TUSER(1'b0)) u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    end
    localparam string CHK = "g_if.u_chk";
`include "xcheck_case.svh"

    task automatic idle();
        g_if.intf.tvalid = 1'b0;
        g_if.intf.tready = 1'b1;
        g_if.intf.tdata = '0;
        g_if.intf.tstrb = '1;
        g_if.intf.tkeep = '1;
        g_if.intf.tlast = 1'b0;
        g_if.intf.tid = '0;
        g_if.intf.tdest = '0;
        g_if.intf.tuser = '0;
    endtask

    task automatic all_x();
        g_if.intf.tvalid = 1'bx;
        g_if.intf.tready = 1'bx;
        g_if.intf.tdata = 'x;
        g_if.intf.tstrb = 'x;
        g_if.intf.tkeep = 'x;
        g_if.intf.tlast = 1'bx;
        g_if.intf.tid = 'x;
        g_if.intf.tdest = 'x;
        g_if.intf.tuser = 'x;
    endtask

    task automatic armed();
        rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
    endtask

    initial begin
        case (CASE)
            0: begin armed(); g_if.intf.tvalid = 1'bx; cycles(1); idle(); end
            1: begin armed(); g_if.intf.tready = 1'bx; cycles(1); idle(); end
            2: begin // tdata X while tvalid is high, twice
                armed();
                g_if.intf.tvalid = 1'b1; g_if.intf.tdata = 'x; cycles(1); idle(); cycles(2);
                g_if.intf.tvalid = 1'b1; g_if.intf.tdata = 'x; cycles(1); idle();
            end
            3: begin armed(); g_if.intf.tdata = 'x; cycles(3); idle(); end
            4: begin armed(); g_if.intf.tvalid = 1'b1; g_if.intf.tstrb = 'x; cycles(1); idle(); end
            5: begin armed(); g_if.intf.tvalid = 1'b1; g_if.intf.tkeep = 'x; cycles(1); idle(); end
            6: begin armed(); g_if.intf.tvalid = 1'b1; g_if.intf.tlast = 1'bx; cycles(1); idle(); end
            7: begin armed(); g_if.intf.tvalid = 1'b1; g_if.intf.tid = 'x; cycles(1); idle(); end
            8: begin armed(); g_if.intf.tvalid = 1'b1; g_if.intf.tdest = 'x; cycles(1); idle(); end
            9: begin armed(); g_if.intf.tvalid = 1'b1; g_if.intf.tuser = 'x; cycles(1); idle(); end
            10: begin // every payload signal X while tvalid is low
                armed(); all_x(); g_if.intf.tvalid = 1'b0; g_if.intf.tready = 1'b1; cycles(3); idle();
            end
            11: begin
                rst_n = 1'b1; all_x(); cycles(3);
                rst_n = 1'b0; cycles(2);
                idle(); rst_n = 1'b1; cycles(3);
                rst_n = 1'b0; all_x(); cycles(3);
                idle(); rst_n = 1'b1; cycles(3);
            end
            12: begin
                rst_n = 1'bx; all_x(); cycles(3);
                rst_n = 1'b1; cycles(3); idle();
            end
            13: begin idle(); delta_reset(); cycles(3); g_if.intf.tvalid = 1'bx; cycles(1); idle(); end
            14: begin // the unbound tuser placeholder X while tvalid is high
                armed(); g_if.intf.tvalid = 1'b1; g_if.intf.tuser = 'x; cycles(3); idle();
            end
        endcase
    end
endmodule

// raw and status have the same signal and the same unqualified check.
module data_case #(parameter bit STATUS = 0, parameter int CASE = 0, parameter int EXP = 0,
                   parameter string SIG = "", parameter string NAME = "") (input logic clk);
    typedef struct packed {
        logic [3:0] hi;
        logic [3:0] lo;
    } data_t;
    logic rst_n;
    data_t data;
    if (STATUS) begin : g_if
        status_if #(.data_t(data_t)) intf();
        assign intf.data = data;
        status_xcheck u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    end else begin : g_if
        raw_if #(.data_t(data_t)) intf();
        assign intf.data = data;
        raw_xcheck u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    end
    localparam string CHK = "g_if.u_chk";
`include "xcheck_case.svh"

    initial begin
        case (CASE)
            0: begin // data X twice
                rst_n = 1'b1; data = '0; reset_pulse(); cycles(2);
                data = 'x; cycles(1); data = '0; cycles(2);
                data = 'x; cycles(1); data = '0;
            end
            1: begin
                rst_n = 1'b1; data = 'x; cycles(3);
                rst_n = 1'b0; cycles(2);
                data = '0; rst_n = 1'b1; cycles(3);
                rst_n = 1'b0; data = 'x; cycles(3);
                data = '0; rst_n = 1'b1; cycles(3);
            end
            2: begin
                rst_n = 1'bx; data = 'x; cycles(3);
                rst_n = 1'b1; cycles(3); data = '0;
            end
            3: begin data = '0; delta_reset(); cycles(3); data = 'x; cycles(1); data = '0; end
        endcase
    end
endmodule

// push_ack has the same shape as rdy_vld: push qualifies data.
module pa_case #(parameter int CASE = 0, parameter int EXP = 0,
                 parameter string SIG = "", parameter string NAME = "") (input logic clk);
    typedef struct packed {
        logic [3:0] hi;
        logic [3:0] lo;
    } data_t;
    logic rst_n;
    push_ack_if #(.data_t(data_t)) intf();
    push_ack_xcheck u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    localparam string CHK = "u_chk";
`include "xcheck_case.svh"

    task automatic idle();
        intf.push = 1'b0;
        intf.ack = 1'b0;
        intf.data = '0;
    endtask

    task automatic all_x();
        intf.push = 1'bx;
        intf.ack = 1'bx;
        intf.data = 'x;
    endtask

    task automatic armed();
        rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
    endtask

    initial begin
        case (CASE)
            0: begin // data X while push is high, twice
                armed();
                intf.push = 1'b1; intf.data = 'x; cycles(1); idle(); cycles(2);
                intf.push = 1'b1; intf.data = 'x; cycles(1); idle();
            end
            1: begin armed(); intf.data = 'x; cycles(3); idle(); end
            2: begin armed(); intf.push = 1'bx; cycles(1); idle(); end
            3: begin armed(); intf.ack = 1'bx; cycles(1); idle(); end
            4: begin
                rst_n = 1'b1; all_x(); cycles(3);
                rst_n = 1'b0; cycles(2);
                idle(); rst_n = 1'b1; cycles(3);
                rst_n = 1'b0; all_x(); cycles(3);
                idle(); rst_n = 1'b1; cycles(3);
            end
            5: begin
                rst_n = 1'bx; all_x(); cycles(3);
                rst_n = 1'b1; cycles(3); idle();
            end
            6: begin idle(); delta_reset(); cycles(3); intf.push = 1'bx; cycles(1); idle(); end
        endcase
    end
endmodule

module na_case #(parameter int CASE = 0, parameter int EXP = 0,
                 parameter string SIG = "", parameter string NAME = "") (input logic clk);
    logic rst_n;
    notify_ack_if intf();
    notify_ack_xcheck u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    localparam string CHK = "u_chk";
`include "xcheck_case.svh"

    task automatic idle();
        intf.notify = 1'b0;
        intf.ack = 1'b0;
    endtask

    task automatic all_x();
        intf.notify = 1'bx;
        intf.ack = 1'bx;
    endtask

    task automatic armed();
        rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
    endtask

    initial begin
        case (CASE)
            0: begin armed(); intf.notify = 1'bx; cycles(1); idle(); end
            1: begin armed(); intf.ack = 1'bx; cycles(1); idle(); end
            2: begin
                rst_n = 1'b1; all_x(); cycles(3);
                rst_n = 1'b0; cycles(2);
                idle(); rst_n = 1'b1; cycles(3);
                rst_n = 1'b0; all_x(); cycles(3);
                idle(); rst_n = 1'b1; cycles(3);
            end
            3: begin
                rst_n = 1'bx; all_x(); cycles(3);
                rst_n = 1'b1; cycles(3); idle();
            end
            4: begin idle(); delta_reset(); cycles(3); intf.notify = 1'bx; cycles(1); idle(); end
        endcase
    end
endmodule

module ra_case #(parameter int CASE = 0, parameter int EXP = 0,
                 parameter string SIG = "", parameter string NAME = "") (input logic clk);
    typedef struct packed {
        logic [3:0] hi;
        logic [3:0] lo;
    } data_t;
    typedef logic [5:0] rdata_t;
    logic rst_n;
    req_ack_if #(.data_t(data_t), .rdata_t(rdata_t)) intf();
    req_ack_xcheck u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    localparam string CHK = "u_chk";
`include "xcheck_case.svh"

    task automatic idle();
        intf.req = 1'b0;
        intf.ack = 1'b0;
        intf.data = '0;
        intf.rdata = '0;
    endtask

    task automatic all_x();
        intf.req = 1'bx;
        intf.ack = 1'bx;
        intf.data = 'x;
        intf.rdata = 'x;
    endtask

    task automatic armed();
        rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
    endtask

    initial begin
        case (CASE)
            0: begin // data X while req is high, twice
                armed();
                intf.req = 1'b1; intf.data = 'x; cycles(1); idle(); cycles(2);
                intf.req = 1'b1; intf.data = 'x; cycles(1); idle();
            end
            1: begin armed(); intf.data = 'x; cycles(3); idle(); end
            2: begin armed(); intf.req = 1'bx; cycles(1); idle(); end
            3: begin armed(); intf.ack = 1'bx; cycles(1); idle(); end
            4: begin armed(); intf.req = 1'b1; intf.ack = 1'b1; intf.rdata = 'x; cycles(1); idle(); end
            5: begin armed(); intf.req = 1'b1; intf.rdata = 'x; cycles(3); idle(); end
            6: begin
                rst_n = 1'b1; all_x(); cycles(3);
                rst_n = 1'b0; cycles(2);
                idle(); rst_n = 1'b1; cycles(3);
                rst_n = 1'b0; all_x(); cycles(3);
                idle(); rst_n = 1'b1; cycles(3);
            end
            7: begin
                rst_n = 1'bx; all_x(); cycles(3);
                rst_n = 1'b1; cycles(3); idle();
            end
            8: begin idle(); delta_reset(); cycles(3); intf.req = 1'bx; cycles(1); idle(); end
        endcase
    end
endmodule

module po_case #(parameter int CASE = 0, parameter int EXP = 0,
                 parameter string SIG = "", parameter string NAME = "") (input logic clk);
    typedef struct packed {
        logic [3:0] hi;
        logic [3:0] lo;
    } rdata_t;
    logic rst_n;
    pop_ack_if #(.rdata_t(rdata_t)) intf();
    pop_ack_xcheck u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    localparam string CHK = "u_chk";
`include "xcheck_case.svh"

    task automatic idle();
        intf.pop = 1'b0;
        intf.ack = 1'b0;
        intf.rdata = '0;
    endtask

    task automatic all_x();
        intf.pop = 1'bx;
        intf.ack = 1'bx;
        intf.rdata = 'x;
    endtask

    task automatic armed();
        rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
    endtask

    initial begin
        case (CASE)
            0: begin armed(); intf.pop = 1'bx; cycles(1); idle(); end
            1: begin armed(); intf.ack = 1'bx; cycles(1); idle(); end
            2: begin // rdata X while ack is high, twice
                armed();
                intf.pop = 1'b1; intf.ack = 1'b1; intf.rdata = 'x; cycles(1); idle(); cycles(2);
                intf.pop = 1'b1; intf.ack = 1'b1; intf.rdata = 'x; cycles(1); idle();
            end
            3: begin armed(); intf.pop = 1'b1; intf.rdata = 'x; cycles(3); idle(); end
            4: begin
                rst_n = 1'b1; all_x(); cycles(3);
                rst_n = 1'b0; cycles(2);
                idle(); rst_n = 1'b1; cycles(3);
                rst_n = 1'b0; all_x(); cycles(3);
                idle(); rst_n = 1'b1; cycles(3);
            end
            5: begin
                rst_n = 1'bx; all_x(); cycles(3);
                rst_n = 1'b1; cycles(3); idle();
            end
            6: begin idle(); delta_reset(); cycles(3); intf.pop = 1'bx; cycles(1); idle(); end
        endcase
    end
endmodule

module mem_case #(parameter int CASE = 0, parameter int EXP = 0,
                  parameter string SIG = "", parameter string NAME = "") (input logic clk);
    typedef struct packed {
        logic [3:0] hi;
        logic [3:0] lo;
    } data_t;
    typedef logic [4:0] addr_t;
    logic rst_n;
    memory_if #(.addr_t(addr_t), .data_t(data_t)) intf();
    memory_xcheck u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    localparam string CHK = "u_chk";
`include "xcheck_case.svh"

    task automatic idle();
        intf.enable = 1'b0;
        intf.wr_en = 1'b0;
        intf.addr = '0;
        intf.write_data = '0;
        intf.read_data = '0;
    endtask

    task automatic all_x();
        intf.enable = 1'bx;
        intf.wr_en = 1'bx;
        intf.addr = 'x;
        intf.write_data = 'x;
        intf.read_data = 'x;
    endtask

    task automatic armed();
        rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
    endtask

    task automatic write(addr_t a);
        intf.enable = 1'b1; intf.wr_en = 1'b1; intf.addr = a; cycles(1); idle();
    endtask

    // A read on one clock; the next clock carries its read_data.
    task automatic read(addr_t a);
        intf.enable = 1'b1; intf.wr_en = 1'b0; intf.addr = a; cycles(1); idle();
    endtask

    initial begin
        case (CASE)
            0: begin armed(); intf.enable = 1'bx; cycles(1); idle(); end
            1: begin armed(); intf.enable = 1'b1; intf.addr = 'x; cycles(1); idle(); end
            2: begin armed(); intf.addr = 'x; cycles(3); idle(); end
            3: begin armed(); intf.enable = 1'b1; intf.wr_en = 1'bx; cycles(1); idle(); end
            4: begin // write_data X on a write, twice
                armed();
                intf.enable = 1'b1; intf.wr_en = 1'b1; intf.write_data = 'x; cycles(1); idle(); cycles(2);
                intf.enable = 1'b1; intf.wr_en = 1'b1; intf.write_data = 'x; cycles(1); idle();
            end
            5: begin armed(); intf.enable = 1'b1; intf.write_data = 'x; cycles(3); idle(); end
            6: begin armed(); read(3); intf.read_data = 'x; cycles(1); idle(); read(4); end
            7: begin // read_data X while idle and after writes
                armed(); intf.read_data = 'x; cycles(2);
                intf.enable = 1'b1; intf.wr_en = 1'b1; cycles(2);
                idle(); intf.read_data = 'x; cycles(2); idle();
            end
            8: begin armed(); write(3); read(3); cycles(1); intf.read_data = 'x; cycles(2); idle(); end
            9: begin
                rst_n = 1'b1; all_x(); cycles(3);
                rst_n = 1'b0; cycles(2);
                idle(); rst_n = 1'b1; cycles(3);
                rst_n = 1'b0; all_x(); cycles(3);
                idle(); rst_n = 1'b1; cycles(3);
            end
            10: begin
                rst_n = 1'bx; all_x(); cycles(3);
                rst_n = 1'b1; cycles(3); idle();
            end
            11: begin idle(); delta_reset(); cycles(3); intf.enable = 1'bx; cycles(1); idle(); end
            12: begin armed(); read(3); intf.read_data = 'x; write(3); end
            13: begin armed(); read(3); intf.read_data = 'x; write(4); end
            // The checker's final block would report too, but its order
            // against this case's final block is undefined.
            14: begin armed(); read(3); intf.read_data = 'x; cycles(1); idle(); cycles(3); u_chk.xzEndOfRun(); end
            15: begin
                armed(); read(3); intf.read_data = 'x; cycles(1); idle();
                reset_pulse(); cycles(2); u_chk.xzEndOfRun();
            end
        endcase
    end
endmodule

module er_case #(parameter int CASE = 0, parameter int EXP = 0,
                 parameter string SIG = "", parameter string NAME = "") (input logic clk);
    typedef struct packed {
        logic [3:0] hi;
        logic [3:0] lo;
    } data_t;
    logic rst_n;
    external_reg_if #(.data_t(data_t)) intf();
    external_reg_xcheck u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    localparam string CHK = "u_chk";
`include "xcheck_case.svh"

    task automatic idle();
        intf.write = '0;
        intf.wdata = '0;
        intf.rdata = '0;
    endtask

    task automatic all_x();
        intf.write = 'x;
        intf.wdata = 'x;
        intf.rdata = 'x;
    endtask

    task automatic armed();
        rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
    endtask

    initial begin
        case (CASE)
            0: begin armed(); intf.write = 'x; cycles(1); idle(); end
            1: begin armed(); intf.rdata = 'x; cycles(1); idle(); end
            2: begin // wdata X on a write, twice
                armed();
                intf.write = 2'b01; intf.wdata = 'x; cycles(1); idle(); cycles(2);
                intf.write = 2'b01; intf.wdata = 'x; cycles(1); idle();
            end
            3: begin armed(); intf.wdata = 'x; cycles(3); idle(); end
            4: begin armed(); intf.write = 2'b10; intf.wdata = 'x; cycles(1); idle(); end
            5: begin
                rst_n = 1'b1; all_x(); cycles(3);
                rst_n = 1'b0; cycles(2);
                idle(); rst_n = 1'b1; cycles(3);
                rst_n = 1'b0; all_x(); cycles(3);
                idle(); rst_n = 1'b1; cycles(3);
            end
            6: begin
                rst_n = 1'bx; all_x(); cycles(3);
                rst_n = 1'b1; cycles(3); idle();
            end
            7: begin idle(); delta_reset(); cycles(3); intf.write = 'x; cycles(1); idle(); end
        endcase
    end
endmodule

module axr_case #(parameter int CASE = 0, parameter int EXP = 0,
                  parameter string SIG = "", parameter string NAME = "",
                  parameter bit BOUND = 1'b1) (input logic clk);
    logic rst_n;
    if (BOUND) begin : g_if
        axi_read_if #(.addr_t(logic [7:0]), .data_t(logic [15:0]), .aruser_t(logic [1:0]),
                      .ruser_t(logic [2:0]), .id_t(logic [1:0])) intf();
        axi_read_xcheck #(.CHECK_ARID(1'b1), .CHECK_ARUSER(1'b1), .CHECK_RID(1'b1), .CHECK_RUSER(1'b1))
            u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    end else begin : g_if
        axi_read_if #(.addr_t(logic [7:0]), .data_t(logic [15:0])) intf();
        axi_read_xcheck #(.CHECK_ARID(1'b0), .CHECK_ARUSER(1'b0), .CHECK_RID(1'b0), .CHECK_RUSER(1'b0))
            u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    end
    localparam string CHK = "g_if.u_chk";
`include "xcheck_case.svh"

    task automatic idle();
        g_if.intf.arvalid = 1'b0;
        g_if.intf.arready = 1'b1;
        g_if.intf.arid = '0;
        g_if.intf.araddr = '0;
        g_if.intf.arlen = '0;
        g_if.intf.arsize = '0;
        g_if.intf.arburst = '0;
        g_if.intf.aruser = '0;
        g_if.intf.rvalid = 1'b0;
        g_if.intf.rready = 1'b1;
        g_if.intf.rid = '0;
        g_if.intf.rdata = '0;
        g_if.intf.rresp = '0;
        g_if.intf.rlast = 1'b0;
        g_if.intf.ruser = '0;
    endtask

    task automatic ar_x();
        g_if.intf.arid = 'x;
        g_if.intf.araddr = 'x;
        g_if.intf.arlen = 'x;
        g_if.intf.arsize = 'x;
        g_if.intf.arburst = 'x;
        g_if.intf.aruser = 'x;
    endtask

    task automatic r_x();
        g_if.intf.rid = 'x;
        g_if.intf.rdata = 'x;
        g_if.intf.rresp = 'x;
        g_if.intf.rlast = 1'bx;
        g_if.intf.ruser = 'x;
    endtask

    task automatic all_x();
        g_if.intf.arvalid = 1'bx;
        g_if.intf.arready = 1'bx;
        g_if.intf.rvalid = 1'bx;
        g_if.intf.rready = 1'bx;
        ar_x();
        r_x();
    endtask

    task automatic armed();
        rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
    endtask

    initial begin
        case (CASE)
            0: begin armed(); g_if.intf.arvalid = 1'bx; cycles(1); idle(); end
            1: begin armed(); g_if.intf.arready = 1'bx; cycles(1); idle(); end
            2: begin armed(); g_if.intf.rvalid = 1'bx; cycles(1); idle(); end
            3: begin armed(); g_if.intf.rready = 1'bx; cycles(1); idle(); end
            4: begin // araddr X while arvalid is high, twice
                armed();
                g_if.intf.arvalid = 1'b1; g_if.intf.araddr = 'x; cycles(1); idle(); cycles(2);
                g_if.intf.arvalid = 1'b1; g_if.intf.araddr = 'x; cycles(1); idle();
            end
            5: begin armed(); g_if.intf.araddr = 'x; cycles(3); idle(); end
            6: begin armed(); g_if.intf.arvalid = 1'b1; g_if.intf.arlen = 'x; cycles(1); idle(); end
            7: begin armed(); g_if.intf.arvalid = 1'b1; g_if.intf.arsize = 'x; cycles(1); idle(); end
            8: begin armed(); g_if.intf.arvalid = 1'b1; g_if.intf.arburst = 'x; cycles(1); idle(); end
            9: begin armed(); g_if.intf.arvalid = 1'b1; g_if.intf.arid = 'x; cycles(1); idle(); end
            10: begin armed(); g_if.intf.arvalid = 1'b1; g_if.intf.aruser = 'x; cycles(1); idle(); end
            11: begin armed(); ar_x(); cycles(3); idle(); end
            12: begin // rdata X while rvalid is high, twice
                armed();
                g_if.intf.rvalid = 1'b1; g_if.intf.rdata = 'x; cycles(1); idle(); cycles(2);
                g_if.intf.rvalid = 1'b1; g_if.intf.rdata = 'x; cycles(1); idle();
            end
            13: begin armed(); g_if.intf.rdata = 'x; cycles(3); idle(); end
            14: begin armed(); g_if.intf.rvalid = 1'b1; g_if.intf.rresp = 'x; cycles(1); idle(); end
            15: begin armed(); g_if.intf.rvalid = 1'b1; g_if.intf.rlast = 1'bx; cycles(1); idle(); end
            16: begin armed(); g_if.intf.rvalid = 1'b1; g_if.intf.rid = 'x; cycles(1); idle(); end
            17: begin armed(); g_if.intf.rvalid = 1'b1; g_if.intf.ruser = 'x; cycles(1); idle(); end
            18: begin armed(); r_x(); cycles(3); idle(); end
            19: begin
                rst_n = 1'b1; all_x(); cycles(3);
                rst_n = 1'b0; cycles(2);
                idle(); rst_n = 1'b1; cycles(3);
                rst_n = 1'b0; all_x(); cycles(3);
                idle(); rst_n = 1'b1; cycles(3);
            end
            20: begin
                rst_n = 1'bx; all_x(); cycles(3);
                rst_n = 1'b1; cycles(3); idle();
            end
            21: begin idle(); delta_reset(); cycles(3); g_if.intf.arvalid = 1'bx; cycles(1); idle(); end
            22: begin // the unbound arid and aruser placeholders X while arvalid is high
                armed(); g_if.intf.arvalid = 1'b1; g_if.intf.arid = 'x; g_if.intf.aruser = 'x; cycles(3); idle();
            end
            23: begin // the unbound rid and ruser placeholders X while rvalid is high
                armed(); g_if.intf.rvalid = 1'b1; g_if.intf.rid = 'x; g_if.intf.ruser = 'x; cycles(3); idle();
            end
        endcase
    end
endmodule

module axw_case #(parameter int CASE = 0, parameter int EXP = 0,
                  parameter string SIG = "", parameter string NAME = "",
                  parameter bit BOUND = 1'b1) (input logic clk);
    logic rst_n;
    if (BOUND) begin : g_if
        axi_write_if #(.addr_t(logic [7:0]), .data_t(logic [15:0]), .strb_t(logic [1:0]), .awuser_t(logic [1:0]),
                       .wuser_t(logic [2:0]), .buser_t(logic [3:0]), .id_t(logic [1:0])) intf();
        axi_write_xcheck #(.CHECK_AWID(1'b1), .CHECK_AWUSER(1'b1), .CHECK_WID(1'b1), .CHECK_WUSER(1'b1),
                           .CHECK_BID(1'b1), .CHECK_BUSER(1'b1))
            u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    end else begin : g_if
        axi_write_if #(.addr_t(logic [7:0]), .data_t(logic [15:0]), .strb_t(logic [1:0])) intf();
        axi_write_xcheck #(.CHECK_AWID(1'b0), .CHECK_AWUSER(1'b0), .CHECK_WID(1'b0), .CHECK_WUSER(1'b0),
                           .CHECK_BID(1'b0), .CHECK_BUSER(1'b0))
            u_chk (.clk(clk), .rst_n(rst_n), .intf(intf));
    end
    localparam string CHK = "g_if.u_chk";
`include "xcheck_case.svh"

    task automatic idle();
        g_if.intf.awvalid = 1'b0;
        g_if.intf.awready = 1'b1;
        g_if.intf.awid = '0;
        g_if.intf.awaddr = '0;
        g_if.intf.awlen = '0;
        g_if.intf.awsize = '0;
        g_if.intf.awburst = '0;
        g_if.intf.awuser = '0;
        g_if.intf.wvalid = 1'b0;
        g_if.intf.wready = 1'b1;
        g_if.intf.wid = '0;
        g_if.intf.wdata = '0;
        g_if.intf.wstrb = '0;
        g_if.intf.wlast = 1'b0;
        g_if.intf.wuser = '0;
        g_if.intf.bvalid = 1'b0;
        g_if.intf.bready = 1'b1;
        g_if.intf.bid = '0;
        g_if.intf.bresp = '0;
        g_if.intf.buser = '0;
    endtask

    task automatic aw_x();
        g_if.intf.awid = 'x;
        g_if.intf.awaddr = 'x;
        g_if.intf.awlen = 'x;
        g_if.intf.awsize = 'x;
        g_if.intf.awburst = 'x;
        g_if.intf.awuser = 'x;
    endtask

    task automatic w_x();
        g_if.intf.wid = 'x;
        g_if.intf.wdata = 'x;
        g_if.intf.wstrb = 'x;
        g_if.intf.wlast = 1'bx;
        g_if.intf.wuser = 'x;
    endtask

    task automatic b_x();
        g_if.intf.bid = 'x;
        g_if.intf.bresp = 'x;
        g_if.intf.buser = 'x;
    endtask

    task automatic all_x();
        g_if.intf.awvalid = 1'bx;
        g_if.intf.awready = 1'bx;
        g_if.intf.wvalid = 1'bx;
        g_if.intf.wready = 1'bx;
        g_if.intf.bvalid = 1'bx;
        g_if.intf.bready = 1'bx;
        aw_x();
        w_x();
        b_x();
    endtask

    task automatic armed();
        rst_n = 1'b1; idle(); reset_pulse(); cycles(2);
    endtask

    initial begin
        case (CASE)
            0: begin armed(); g_if.intf.awvalid = 1'bx; cycles(1); idle(); end
            1: begin armed(); g_if.intf.awready = 1'bx; cycles(1); idle(); end
            2: begin armed(); g_if.intf.wvalid = 1'bx; cycles(1); idle(); end
            3: begin armed(); g_if.intf.wready = 1'bx; cycles(1); idle(); end
            4: begin armed(); g_if.intf.bvalid = 1'bx; cycles(1); idle(); end
            5: begin armed(); g_if.intf.bready = 1'bx; cycles(1); idle(); end
            6: begin // awaddr X while awvalid is high, twice
                armed();
                g_if.intf.awvalid = 1'b1; g_if.intf.awaddr = 'x; cycles(1); idle(); cycles(2);
                g_if.intf.awvalid = 1'b1; g_if.intf.awaddr = 'x; cycles(1); idle();
            end
            7: begin armed(); g_if.intf.awaddr = 'x; cycles(3); idle(); end
            8: begin armed(); g_if.intf.awvalid = 1'b1; g_if.intf.awlen = 'x; cycles(1); idle(); end
            9: begin armed(); g_if.intf.awvalid = 1'b1; g_if.intf.awsize = 'x; cycles(1); idle(); end
            10: begin armed(); g_if.intf.awvalid = 1'b1; g_if.intf.awburst = 'x; cycles(1); idle(); end
            11: begin armed(); g_if.intf.awvalid = 1'b1; g_if.intf.awid = 'x; cycles(1); idle(); end
            12: begin armed(); g_if.intf.awvalid = 1'b1; g_if.intf.awuser = 'x; cycles(1); idle(); end
            13: begin armed(); aw_x(); cycles(3); idle(); end
            14: begin // wdata X while wvalid is high, twice
                armed();
                g_if.intf.wvalid = 1'b1; g_if.intf.wdata = 'x; cycles(1); idle(); cycles(2);
                g_if.intf.wvalid = 1'b1; g_if.intf.wdata = 'x; cycles(1); idle();
            end
            15: begin armed(); g_if.intf.wdata = 'x; cycles(3); idle(); end
            16: begin armed(); g_if.intf.wvalid = 1'b1; g_if.intf.wstrb = 'x; cycles(1); idle(); end
            17: begin armed(); g_if.intf.wvalid = 1'b1; g_if.intf.wlast = 1'bx; cycles(1); idle(); end
            18: begin armed(); g_if.intf.wvalid = 1'b1; g_if.intf.wid = 'x; cycles(1); idle(); end
            19: begin armed(); g_if.intf.wvalid = 1'b1; g_if.intf.wuser = 'x; cycles(1); idle(); end
            20: begin armed(); w_x(); cycles(3); idle(); end
            21: begin // bresp X while bvalid is high, twice
                armed();
                g_if.intf.bvalid = 1'b1; g_if.intf.bresp = 'x; cycles(1); idle(); cycles(2);
                g_if.intf.bvalid = 1'b1; g_if.intf.bresp = 'x; cycles(1); idle();
            end
            22: begin armed(); g_if.intf.bresp = 'x; cycles(3); idle(); end
            23: begin armed(); g_if.intf.bvalid = 1'b1; g_if.intf.bid = 'x; cycles(1); idle(); end
            24: begin armed(); g_if.intf.bvalid = 1'b1; g_if.intf.buser = 'x; cycles(1); idle(); end
            25: begin armed(); b_x(); cycles(3); idle(); end
            26: begin
                rst_n = 1'b1; all_x(); cycles(3);
                rst_n = 1'b0; cycles(2);
                idle(); rst_n = 1'b1; cycles(3);
                rst_n = 1'b0; all_x(); cycles(3);
                idle(); rst_n = 1'b1; cycles(3);
            end
            27: begin
                rst_n = 1'bx; all_x(); cycles(3);
                rst_n = 1'b1; cycles(3); idle();
            end
            28: begin idle(); delta_reset(); cycles(3); g_if.intf.awvalid = 1'bx; cycles(1); idle(); end
            29: begin // the unbound awid and awuser placeholders X while awvalid is high
                armed(); g_if.intf.awvalid = 1'b1; g_if.intf.awid = 'x; g_if.intf.awuser = 'x; cycles(3); idle();
            end
            30: begin // the unbound wid and wuser placeholders X while wvalid is high
                armed(); g_if.intf.wvalid = 1'b1; g_if.intf.wid = 'x; g_if.intf.wuser = 'x; cycles(3); idle();
            end
            31: begin // the unbound bid and buser placeholders X while bvalid is high
                armed(); g_if.intf.bvalid = 1'b1; g_if.intf.bid = 'x; g_if.intf.buser = 'x; cycles(3); idle();
            end
        endcase
    end
endmodule

module xcheck_tb;
    logic clk = 1'b0;
    // The first rising edge is at 5 ns, after the time-0 delta resets.
    always #5 clk = ~clk;

    localparam int CASES = 7 + 16 + 15 + 4 + 4 + 7 + 5 + 9 + 7 + 16 + 8 + 24 + 32;

    rv_case #(0, 1, "data", "rdy_vld data X while vld, twice") rv0 (clk);
    rv_case #(1, 0, "", "rdy_vld data X while !vld") rv1 (clk);
    rv_case #(2, 1, "vld", "rdy_vld vld X") rv2 (clk);
    rv_case #(3, 1, "rdy", "rdy_vld rdy X") rv3 (clk);
    rv_case #(4, 0, "", "rdy_vld X before arming and in reset") rv4 (clk);
    rv_case #(5, 0, "", "rdy_vld power-on X reset") rv5 (clk);
    rv_case #(6, 1, "vld", "rdy_vld reset released before a clock edge") rv6 (clk);

    apb_case #(0, 1, "psel", "apb psel X") apb0 (clk);
    apb_case #(1, 1, "penable", "apb penable X") apb1 (clk);
    apb_case #(2, 1, "pready", "apb pready X") apb2 (clk);
    apb_case #(3, 1, "paddr", "apb paddr X while psel") apb3 (clk);
    apb_case #(4, 0, "", "apb paddr X while !psel") apb4 (clk);
    apb_case #(5, 1, "pwrite", "apb pwrite X while psel") apb5 (clk);
    apb_case #(6, 1, "pwdata", "apb pwdata X while psel && pwrite, twice") apb6 (clk);
    apb_case #(7, 0, "", "apb pwdata X while psel && !pwrite") apb7 (clk);
    apb_case #(8, 1, "pslverr", "apb pslverr X on completion") apb8 (clk);
    apb_case #(9, 0, "", "apb pslverr X while !pready") apb9 (clk);
    apb_case #(10, 1, "prdata", "apb prdata X on read completion") apb10 (clk);
    apb_case #(11, 0, "", "apb prdata X on write completion") apb11 (clk);
    apb_case #(12, 0, "", "apb prdata X on read while !pready") apb12 (clk);
    apb_case #(13, 0, "", "apb X before arming and in reset") apb13 (clk);
    apb_case #(14, 0, "", "apb power-on X reset") apb14 (clk);
    apb_case #(15, 1, "psel", "apb reset released before a clock edge") apb15 (clk);

    axis_case #(0, 1, "tvalid", "axi4_stream tvalid X") axis0 (clk);
    axis_case #(1, 1, "tready", "axi4_stream tready X") axis1 (clk);
    axis_case #(2, 1, "tdata", "axi4_stream tdata X while tvalid, twice") axis2 (clk);
    axis_case #(3, 0, "", "axi4_stream tdata X while !tvalid") axis3 (clk);
    axis_case #(4, 1, "tstrb", "axi4_stream tstrb X while tvalid") axis4 (clk);
    axis_case #(5, 1, "tkeep", "axi4_stream tkeep X while tvalid") axis5 (clk);
    axis_case #(6, 1, "tlast", "axi4_stream tlast X while tvalid") axis6 (clk);
    axis_case #(7, 1, "tid", "axi4_stream tid X while tvalid") axis7 (clk);
    axis_case #(8, 1, "tdest", "axi4_stream tdest X while tvalid") axis8 (clk);
    axis_case #(9, 1, "tuser", "axi4_stream bound tuser X while tvalid") axis9 (clk);
    axis_case #(10, 0, "", "axi4_stream payload X while !tvalid") axis10 (clk);
    axis_case #(11, 0, "", "axi4_stream X before arming and in reset") axis11 (clk);
    axis_case #(12, 0, "", "axi4_stream power-on X reset") axis12 (clk);
    axis_case #(13, 1, "tvalid", "axi4_stream reset released before a clock edge") axis13 (clk);
    axis_case #(14, 0, "", "axi4_stream unbound tuser X while tvalid", 1'b0) axis14 (clk);

    data_case #(0, 0, 1, "data", "raw data X, twice") raw0 (clk);
    data_case #(0, 1, 0, "", "raw X before arming and in reset") raw1 (clk);
    data_case #(0, 2, 0, "", "raw power-on X reset") raw2 (clk);
    data_case #(0, 3, 1, "data", "raw reset released before a clock edge") raw3 (clk);

    data_case #(1, 0, 1, "data", "status data X, twice") st0 (clk);
    data_case #(1, 1, 0, "", "status X before arming and in reset") st1 (clk);
    data_case #(1, 2, 0, "", "status power-on X reset") st2 (clk);
    data_case #(1, 3, 1, "data", "status reset released before a clock edge") st3 (clk);

    pa_case #(0, 1, "data", "push_ack data X while push, twice") pa0 (clk);
    pa_case #(1, 0, "", "push_ack data X while !push") pa1 (clk);
    pa_case #(2, 1, "push", "push_ack push X") pa2 (clk);
    pa_case #(3, 1, "ack", "push_ack ack X") pa3 (clk);
    pa_case #(4, 0, "", "push_ack X before arming and in reset") pa4 (clk);
    pa_case #(5, 0, "", "push_ack power-on X reset") pa5 (clk);
    pa_case #(6, 1, "push", "push_ack reset released before a clock edge") pa6 (clk);

    na_case #(0, 1, "notify", "notify_ack notify X") na0 (clk);
    na_case #(1, 1, "ack", "notify_ack ack X") na1 (clk);
    na_case #(2, 0, "", "notify_ack X before arming and in reset") na2 (clk);
    na_case #(3, 0, "", "notify_ack power-on X reset") na3 (clk);
    na_case #(4, 1, "notify", "notify_ack reset released before a clock edge") na4 (clk);

    ra_case #(0, 1, "data", "req_ack data X while req, twice") ra0 (clk);
    ra_case #(1, 0, "", "req_ack data X while !req") ra1 (clk);
    ra_case #(2, 1, "req", "req_ack req X") ra2 (clk);
    ra_case #(3, 1, "ack", "req_ack ack X") ra3 (clk);
    ra_case #(4, 1, "rdata", "req_ack rdata X while ack") ra4 (clk);
    ra_case #(5, 0, "", "req_ack rdata X while !ack") ra5 (clk);
    ra_case #(6, 0, "", "req_ack X before arming and in reset") ra6 (clk);
    ra_case #(7, 0, "", "req_ack power-on X reset") ra7 (clk);
    ra_case #(8, 1, "req", "req_ack reset released before a clock edge") ra8 (clk);

    po_case #(0, 1, "pop", "pop_ack pop X") po0 (clk);
    po_case #(1, 1, "ack", "pop_ack ack X") po1 (clk);
    po_case #(2, 1, "rdata", "pop_ack rdata X while ack, twice") po2 (clk);
    po_case #(3, 0, "", "pop_ack rdata X while !ack") po3 (clk);
    po_case #(4, 0, "", "pop_ack X before arming and in reset") po4 (clk);
    po_case #(5, 0, "", "pop_ack power-on X reset") po5 (clk);
    po_case #(6, 1, "pop", "pop_ack reset released before a clock edge") po6 (clk);

    mem_case #(0, 1, "enable", "memory enable X") mem0 (clk);
    mem_case #(1, 1, "addr", "memory addr X while enable") mem1 (clk);
    mem_case #(2, 0, "", "memory addr X while !enable") mem2 (clk);
    mem_case #(3, 1, "wr_en", "memory wr_en X while enable") mem3 (clk);
    mem_case #(4, 1, "write_data", "memory write_data X on a write, twice") mem4 (clk);
    mem_case #(5, 0, "", "memory write_data X on a read") mem5 (clk);
    mem_case #(6, 1, "read_data", "memory read_data X after a read, then a read") mem6 (clk);
    mem_case #(7, 0, "", "memory read_data X while idle and after writes") mem7 (clk);
    mem_case #(8, 0, "", "memory read_data X two clocks after a read") mem8 (clk);
    mem_case #(9, 0, "", "memory X before arming and in reset") mem9 (clk);
    mem_case #(10, 0, "", "memory power-on X reset") mem10 (clk);
    mem_case #(11, 1, "enable", "memory reset released before a clock edge") mem11 (clk);
    mem_case #(12, 0, "", "memory read_data X after a read, then a write of that address") mem12 (clk);
    mem_case #(13, 1, "read_data", "memory read_data X after a read, then a write elsewhere") mem13 (clk);
    mem_case #(14, 1, "read_data", "memory read_data X after a read, then no access to the end") mem14 (clk);
    mem_case #(15, 0, "", "memory read_data X after a read, then a reset") mem15 (clk);

    er_case #(0, 1, "write", "external_reg write X") er0 (clk);
    er_case #(1, 1, "rdata", "external_reg rdata X") er1 (clk);
    er_case #(2, 1, "wdata", "external_reg wdata X on a write, twice") er2 (clk);
    er_case #(3, 0, "", "external_reg wdata X while write is zero") er3 (clk);
    er_case #(4, 1, "wdata", "external_reg wdata X on a write strobe 2'b10") er4 (clk);
    er_case #(5, 0, "", "external_reg X before arming and in reset") er5 (clk);
    er_case #(6, 0, "", "external_reg power-on X reset") er6 (clk);
    er_case #(7, 1, "write", "external_reg reset released before a clock edge") er7 (clk);

    axr_case #(0, 1, "arvalid", "axi_read arvalid X") axr0 (clk);
    axr_case #(1, 1, "arready", "axi_read arready X") axr1 (clk);
    axr_case #(2, 1, "rvalid", "axi_read rvalid X") axr2 (clk);
    axr_case #(3, 1, "rready", "axi_read rready X") axr3 (clk);
    axr_case #(4, 1, "araddr", "axi_read araddr X while arvalid, twice") axr4 (clk);
    axr_case #(5, 0, "", "axi_read araddr X while !arvalid") axr5 (clk);
    axr_case #(6, 1, "arlen", "axi_read arlen X while arvalid") axr6 (clk);
    axr_case #(7, 1, "arsize", "axi_read arsize X while arvalid") axr7 (clk);
    axr_case #(8, 1, "arburst", "axi_read arburst X while arvalid") axr8 (clk);
    axr_case #(9, 1, "arid", "axi_read bound arid X while arvalid") axr9 (clk);
    axr_case #(10, 1, "aruser", "axi_read bound aruser X while arvalid") axr10 (clk);
    axr_case #(11, 0, "", "axi_read AR payload X while !arvalid") axr11 (clk);
    axr_case #(12, 1, "rdata", "axi_read rdata X while rvalid, twice") axr12 (clk);
    axr_case #(13, 0, "", "axi_read rdata X while !rvalid") axr13 (clk);
    axr_case #(14, 1, "rresp", "axi_read rresp X while rvalid") axr14 (clk);
    axr_case #(15, 1, "rlast", "axi_read rlast X while rvalid") axr15 (clk);
    axr_case #(16, 1, "rid", "axi_read bound rid X while rvalid") axr16 (clk);
    axr_case #(17, 1, "ruser", "axi_read bound ruser X while rvalid") axr17 (clk);
    axr_case #(18, 0, "", "axi_read R payload X while !rvalid") axr18 (clk);
    axr_case #(19, 0, "", "axi_read X before arming and in reset") axr19 (clk);
    axr_case #(20, 0, "", "axi_read power-on X reset") axr20 (clk);
    axr_case #(21, 1, "arvalid", "axi_read reset released before a clock edge") axr21 (clk);
    axr_case #(22, 0, "", "axi_read unbound arid and aruser X while arvalid", 1'b0) axr22 (clk);
    axr_case #(23, 0, "", "axi_read unbound rid and ruser X while rvalid", 1'b0) axr23 (clk);

    axw_case #(0, 1, "awvalid", "axi_write awvalid X") axw0 (clk);
    axw_case #(1, 1, "awready", "axi_write awready X") axw1 (clk);
    axw_case #(2, 1, "wvalid", "axi_write wvalid X") axw2 (clk);
    axw_case #(3, 1, "wready", "axi_write wready X") axw3 (clk);
    axw_case #(4, 1, "bvalid", "axi_write bvalid X") axw4 (clk);
    axw_case #(5, 1, "bready", "axi_write bready X") axw5 (clk);
    axw_case #(6, 1, "awaddr", "axi_write awaddr X while awvalid, twice") axw6 (clk);
    axw_case #(7, 0, "", "axi_write awaddr X while !awvalid") axw7 (clk);
    axw_case #(8, 1, "awlen", "axi_write awlen X while awvalid") axw8 (clk);
    axw_case #(9, 1, "awsize", "axi_write awsize X while awvalid") axw9 (clk);
    axw_case #(10, 1, "awburst", "axi_write awburst X while awvalid") axw10 (clk);
    axw_case #(11, 1, "awid", "axi_write bound awid X while awvalid") axw11 (clk);
    axw_case #(12, 1, "awuser", "axi_write bound awuser X while awvalid") axw12 (clk);
    axw_case #(13, 0, "", "axi_write AW payload X while !awvalid") axw13 (clk);
    axw_case #(14, 1, "wdata", "axi_write wdata X while wvalid, twice") axw14 (clk);
    axw_case #(15, 0, "", "axi_write wdata X while !wvalid") axw15 (clk);
    axw_case #(16, 1, "wstrb", "axi_write wstrb X while wvalid") axw16 (clk);
    axw_case #(17, 1, "wlast", "axi_write wlast X while wvalid") axw17 (clk);
    axw_case #(18, 1, "wid", "axi_write bound wid X while wvalid") axw18 (clk);
    axw_case #(19, 1, "wuser", "axi_write bound wuser X while wvalid") axw19 (clk);
    axw_case #(20, 0, "", "axi_write W payload X while !wvalid") axw20 (clk);
    axw_case #(21, 1, "bresp", "axi_write bresp X while bvalid, twice") axw21 (clk);
    axw_case #(22, 0, "", "axi_write bresp X while !bvalid") axw22 (clk);
    axw_case #(23, 1, "bid", "axi_write bound bid X while bvalid") axw23 (clk);
    axw_case #(24, 1, "buser", "axi_write bound buser X while bvalid") axw24 (clk);
    axw_case #(25, 0, "", "axi_write B payload X while !bvalid") axw25 (clk);
    axw_case #(26, 0, "", "axi_write X before arming and in reset") axw26 (clk);
    axw_case #(27, 0, "", "axi_write power-on X reset") axw27 (clk);
    axw_case #(28, 1, "awvalid", "axi_write reset released before a clock edge") axw28 (clk);
    axw_case #(29, 0, "", "axi_write unbound awid and awuser X while awvalid", 1'b0) axw29 (clk);
    axw_case #(30, 0, "", "axi_write unbound wid and wuser X while wvalid", 1'b0) axw30 (clk);
    axw_case #(31, 0, "", "axi_write unbound bid and buser X while bvalid", 1'b0) axw31 (clk);

    initial begin
        $display("XC_CASES %0d", CASES);
        #400 $finish;
    end
endmodule
