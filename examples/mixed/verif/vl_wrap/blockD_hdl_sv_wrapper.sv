`ifndef _BLOCKD_HDL_SV_WRAPPER_SV_GUARD_
`define _BLOCKD_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=blockD
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module blockD_hdl_sv_wrapper
    // Generated Import package statement(s)
    import mixedInclude_package::*;
    import mixedBlockC_package::*;
    import mixed_package::*;
(
    // rdy_vld_if.src
    output bit cStuffIf_vld,
    output bit [4:0] cStuffIf_data,
    input bit cStuffIf_rdy,

    // rdy_vld_if.src
    output bit dee0_vld,
    output bit [6:0] dee0_data,
    input bit dee0_rdy,

    // rdy_vld_if.src
    output bit dee1_vld,
    output bit [6:0] dee1_data,
    input bit dee1_rdy,

    // rdy_vld_if.src
    output bit outD_vld,
    output bit [6:0] outD_data,
    input bit outD_rdy,

    // rdy_vld_if.dst
    input bit inD_vld,
    input bit [6:0] inD_data,
    output bit inD_rdy,

    // req_ack_if.dst
    input bit btod_req,
    input bit [3:0] btod_data,
    output bit btod_ack,
    output bit btod_rdata,

    // status_if.dst
    input bit [6:0] rwD_data,

    // status_if.src
    output bit [3:0] roBsize_data,

    // memory_if.dst
    input bit [4:0] blockBTableExt_write_data,
    output bit [4:0] blockBTableExt_read_data,
    input bit [3:0] blockBTableExt_addr,
    input bit blockBTableExt_enable,
    input bit blockBTableExt_wr_en,

    // memory_if.dst
    input bit [36:0] blockBTable37Bit_write_data,
    output bit [36:0] blockBTable37Bit_read_data,
    input bit [3:0] blockBTable37Bit_addr,
    input bit blockBTable37Bit_enable,
    input bit blockBTable37Bit_wr_en,

    // status_if.dst
    input bit [6:0] rwArr_data,

    // external_reg_if.dst [REGARR_N]
    input bit [6:0] extArr_0_wdata,
    output bit [6:0] extArr_0_rdata,
    input bit [1:0] extArr_0_write,
    input bit [6:0] extArr_1_wdata,
    output bit [6:0] extArr_1_rdata,
    input bit [1:0] extArr_1_write,
    input bit [6:0] extArr_2_wdata,
    output bit [6:0] extArr_2_rdata,
    input bit [1:0] extArr_2_write,
    input bit [6:0] extArr_3_wdata,
    output bit [6:0] extArr_3_rdata,
    input bit [1:0] extArr_3_write,

    // memory_if.src
    output bit [63:0] blockBTable1_write_data,
    input bit [63:0] blockBTable1_read_data,
    output bit [3:0] blockBTable1_addr,
    output bit blockBTable1_enable,
    output bit blockBTable1_wr_en,

    // memory_if.src
    output bit [17:0] blockBTableSP_write_data,
    input bit [17:0] blockBTableSP_read_data,
    output bit [3:0] blockBTableSP_addr,
    output bit blockBTableSP_enable,
    output bit blockBTableSP_wr_en,

    input clk,
    input rst_n
);
    // rdy_vld_if.src
    rdy_vld_if #(.data_t(seeSt)) cStuffIf();

    assign `A2C_HDL_BOUNDARY_DLY cStuffIf_vld = cStuffIf.vld;
    assign `A2C_HDL_BOUNDARY_DLY cStuffIf_data = cStuffIf.data;
    assign `A2C_HDL_BOUNDARY_DLY cStuffIf.rdy = cStuffIf_rdy;

    // rdy_vld_if.src
    rdy_vld_if #(.data_t(dSt)) dee0();

    assign `A2C_HDL_BOUNDARY_DLY dee0_vld = dee0.vld;
    assign `A2C_HDL_BOUNDARY_DLY dee0_data = dee0.data;
    assign `A2C_HDL_BOUNDARY_DLY dee0.rdy = dee0_rdy;

    // rdy_vld_if.src
    rdy_vld_if #(.data_t(dSt)) dee1();

    assign `A2C_HDL_BOUNDARY_DLY dee1_vld = dee1.vld;
    assign `A2C_HDL_BOUNDARY_DLY dee1_data = dee1.data;
    assign `A2C_HDL_BOUNDARY_DLY dee1.rdy = dee1_rdy;

    // rdy_vld_if.src
    rdy_vld_if #(.data_t(dSt)) outD();

    assign `A2C_HDL_BOUNDARY_DLY outD_vld = outD.vld;
    assign `A2C_HDL_BOUNDARY_DLY outD_data = outD.data;
    assign `A2C_HDL_BOUNDARY_DLY outD.rdy = outD_rdy;

    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(dSt)) inD();

    assign `A2C_HDL_BOUNDARY_DLY inD.vld = inD_vld;
    assign `A2C_HDL_BOUNDARY_DLY inD.data = inD_data;
    assign `A2C_HDL_BOUNDARY_DLY inD_rdy = inD.rdy;

    // req_ack_if.dst
    req_ack_if #(.data_t(aSt), .rdata_t(aASt)) btod();

    assign `A2C_HDL_BOUNDARY_DLY btod.req = btod_req;
    assign `A2C_HDL_BOUNDARY_DLY btod.data = btod_data;
    assign `A2C_HDL_BOUNDARY_DLY btod_ack = btod.ack;
    assign `A2C_HDL_BOUNDARY_DLY btod_rdata = btod.rdata;

    // status_if.dst
    status_if #(.data_t(dRegSt)) rwD();

    assign `A2C_HDL_BOUNDARY_DLY rwD.data = rwD_data;

    // status_if.src
    status_if #(.data_t(bSizeRegSt)) roBsize();

    assign `A2C_HDL_BOUNDARY_DLY roBsize_data = roBsize.data;

    // memory_if.dst
    memory_if #(.addr_t(bSizeSt), .data_t(seeSt)) blockBTableExt();

    assign `A2C_HDL_BOUNDARY_DLY blockBTableExt.write_data = blockBTableExt_write_data;
    assign `A2C_HDL_BOUNDARY_DLY blockBTableExt_read_data = blockBTableExt.read_data;
    assign `A2C_HDL_BOUNDARY_DLY blockBTableExt.addr = blockBTableExt_addr;
    assign `A2C_HDL_BOUNDARY_DLY blockBTableExt.enable = blockBTableExt_enable;
    assign `A2C_HDL_BOUNDARY_DLY blockBTableExt.wr_en = blockBTableExt_wr_en;

    // memory_if.dst
    memory_if #(.addr_t(bSizeSt), .data_t(test37BitRegSt)) blockBTable37Bit();

    assign `A2C_HDL_BOUNDARY_DLY blockBTable37Bit.write_data = blockBTable37Bit_write_data;
    assign `A2C_HDL_BOUNDARY_DLY blockBTable37Bit_read_data = blockBTable37Bit.read_data;
    assign `A2C_HDL_BOUNDARY_DLY blockBTable37Bit.addr = blockBTable37Bit_addr;
    assign `A2C_HDL_BOUNDARY_DLY blockBTable37Bit.enable = blockBTable37Bit_enable;
    assign `A2C_HDL_BOUNDARY_DLY blockBTable37Bit.wr_en = blockBTable37Bit_wr_en;

    // status_if.dst
    status_if #(.data_t(dRegSt)) rwArr();

    assign `A2C_HDL_BOUNDARY_DLY rwArr.data = rwArr_data;

    // external_reg_if.dst [REGARR_N]
    external_reg_if #(.data_t(dRegSt)) extArr [REGARR_N]();

    assign `A2C_HDL_BOUNDARY_DLY extArr[0].wdata = extArr_0_wdata;
    assign `A2C_HDL_BOUNDARY_DLY extArr_0_rdata = extArr[0].rdata;
    assign `A2C_HDL_BOUNDARY_DLY extArr[0].write = extArr_0_write;
    assign `A2C_HDL_BOUNDARY_DLY extArr[1].wdata = extArr_1_wdata;
    assign `A2C_HDL_BOUNDARY_DLY extArr_1_rdata = extArr[1].rdata;
    assign `A2C_HDL_BOUNDARY_DLY extArr[1].write = extArr_1_write;
    assign `A2C_HDL_BOUNDARY_DLY extArr[2].wdata = extArr_2_wdata;
    assign `A2C_HDL_BOUNDARY_DLY extArr_2_rdata = extArr[2].rdata;
    assign `A2C_HDL_BOUNDARY_DLY extArr[2].write = extArr_2_write;
    assign `A2C_HDL_BOUNDARY_DLY extArr[3].wdata = extArr_3_wdata;
    assign `A2C_HDL_BOUNDARY_DLY extArr_3_rdata = extArr[3].rdata;
    assign `A2C_HDL_BOUNDARY_DLY extArr[3].write = extArr_3_write;

    // memory_if.src
    memory_if #(.addr_t(bSizeSt), .data_t(bigSt)) blockBTable1();

    assign `A2C_HDL_BOUNDARY_DLY blockBTable1_write_data = blockBTable1.write_data;
    assign `A2C_HDL_BOUNDARY_DLY blockBTable1.read_data = blockBTable1_read_data;
    assign `A2C_HDL_BOUNDARY_DLY blockBTable1_addr = blockBTable1.addr;
    assign `A2C_HDL_BOUNDARY_DLY blockBTable1_enable = blockBTable1.enable;
    assign `A2C_HDL_BOUNDARY_DLY blockBTable1_wr_en = blockBTable1.wr_en;

    // memory_if.src
    memory_if #(.addr_t(bSizeSt), .data_t(nestedSt)) blockBTableSP();

    assign `A2C_HDL_BOUNDARY_DLY blockBTableSP_write_data = blockBTableSP.write_data;
    assign `A2C_HDL_BOUNDARY_DLY blockBTableSP.read_data = blockBTableSP_read_data;
    assign `A2C_HDL_BOUNDARY_DLY blockBTableSP_addr = blockBTableSP.addr;
    assign `A2C_HDL_BOUNDARY_DLY blockBTableSP_enable = blockBTableSP.enable;
    assign `A2C_HDL_BOUNDARY_DLY blockBTableSP_wr_en = blockBTableSP.wr_en;

    blockD dut (
        .cStuffIf(cStuffIf), // rdy_vld_if.src
        .dee0(dee0), // rdy_vld_if.src
        .dee1(dee1), // rdy_vld_if.src
        .outD(outD), // rdy_vld_if.src
        .inD(inD), // rdy_vld_if.dst
        .btod(btod), // req_ack_if.dst
        .rwD(rwD), // status_if.dst
        .roBsize(roBsize), // status_if.src
        .blockBTableExt(blockBTableExt), // memory_if.dst
        .blockBTable37Bit(blockBTable37Bit), // memory_if.dst
        .rwArr(rwArr), // status_if.dst
        .extArr(extArr), // external_reg_if.dst [REGARR_N]
        .blockBTable1(blockBTable1), // memory_if.src
        .blockBTableSP(blockBTableSP), // memory_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : blockD_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _BLOCKD_HDL_SV_WRAPPER_SV_GUARD_
