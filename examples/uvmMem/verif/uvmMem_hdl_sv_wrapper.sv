`ifndef _UVMMEM_HDL_SV_WRAPPER_SV_GUARD_
`define _UVMMEM_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=uvmMem
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module uvmMem_hdl_sv_wrapper
    // Generated Import package statement(s)
    import uvmMem_package::*;
(
    // rdy_vld_if.dst
    input bit cmd_vld,
    input bit [39:0] cmd_data,
    output bit cmd_rdy,

    // rdy_vld_if.src
    output bit out_vld,
    output bit [31:0] out_data,
    input bit out_rdy,

    // memory_if.src
    output bit [31:0] wr_write_data,
    input bit [31:0] wr_read_data,
    output bit [3:0] wr_addr,
    output bit wr_enable,
    output bit wr_wr_en,

    // memory_if.src
    output bit [31:0] rd_write_data,
    input bit [31:0] rd_read_data,
    output bit [3:0] rd_addr,
    output bit rd_enable,
    output bit rd_wr_en,

    input clk,
    input rst_n
);
    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(uvmMemCmdSt)) cmd();

    assign `A2C_HDL_BOUNDARY_DLY cmd.vld = cmd_vld;
    assign `A2C_HDL_BOUNDARY_DLY cmd.data = cmd_data;
    assign `A2C_HDL_BOUNDARY_DLY cmd_rdy = cmd.rdy;

    // rdy_vld_if.src
    rdy_vld_if #(.data_t(uvmMemWordSt)) out();

    assign `A2C_HDL_BOUNDARY_DLY out_vld = out.vld;
    assign `A2C_HDL_BOUNDARY_DLY out_data = out.data;
    assign `A2C_HDL_BOUNDARY_DLY out.rdy = out_rdy;

    // memory_if.src
    memory_if #(.addr_t(uvmMemAddrSt), .data_t(uvmMemWordSt)) wr();

    assign `A2C_HDL_BOUNDARY_DLY wr_write_data = wr.write_data;
    assign `A2C_HDL_BOUNDARY_DLY wr.read_data = wr_read_data;
    assign `A2C_HDL_BOUNDARY_DLY wr_addr = wr.addr;
    assign `A2C_HDL_BOUNDARY_DLY wr_enable = wr.enable;
    assign `A2C_HDL_BOUNDARY_DLY wr_wr_en = wr.wr_en;

    // memory_if.src
    memory_if #(.addr_t(uvmMemAddrSt), .data_t(uvmMemWordSt)) rd();

    assign `A2C_HDL_BOUNDARY_DLY rd_write_data = rd.write_data;
    assign `A2C_HDL_BOUNDARY_DLY rd.read_data = rd_read_data;
    assign `A2C_HDL_BOUNDARY_DLY rd_addr = rd.addr;
    assign `A2C_HDL_BOUNDARY_DLY rd_enable = rd.enable;
    assign `A2C_HDL_BOUNDARY_DLY rd_wr_en = rd.wr_en;

    uvmMem dut (
        .cmd(cmd), // rdy_vld_if.dst
        .out(out), // rdy_vld_if.src
        .wr(wr), // memory_if.src
        .rd(rd), // memory_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

    `ifndef VERILATOR
    rdy_vld_xcheck cmd_xcheck (.clk(clk), .rst_n(rst_n), .intf(cmd));
    rdy_vld_xcheck out_xcheck (.clk(clk), .rst_n(rst_n), .intf(out));
    memory_xcheck wr_xcheck (.clk(clk), .rst_n(rst_n), .intf(wr));
    memory_xcheck rd_xcheck (.clk(clk), .rst_n(rst_n), .intf(rd));
    `endif

endmodule : uvmMem_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _UVMMEM_HDL_SV_WRAPPER_SV_GUARD_
