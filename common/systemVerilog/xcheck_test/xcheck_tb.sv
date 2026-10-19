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

module xcheck_tb;
    logic clk = 1'b0;
    // The first rising edge is at 5 ns, after the time-0 delta resets.
    always #5 clk = ~clk;

    localparam int CASES = 7 + 16 + 15 + 4 + 4 + 7 + 5 + 9 + 7;

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

    initial begin
        $display("XC_CASES %0d", CASES);
        #400 $finish;
    end
endmodule
