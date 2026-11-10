// GENERATED_CODE_PARAM --block=blockBRegs
// GENERATED_CODE_BEGIN --template=moduleRegs
module blockBRegs
    // Generated Import package statement(s)
    import mixedInclude_package::*;
    import mixedBlockC_package::*;
    import mixed_package::*;
    #(
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst apbReg,
        status_if.src rwD,
        status_if.dst roBsize,
        memory_if.src blockBTableExt,
        memory_if.src blockBTable37Bit,
        status_if.src rwArr [REGARR_N],
        external_reg_if.src extArr [REGARR_N],
        memory_if.src blockBTable1,
        input clk,
        input rst_n
    );

    apbAddrSt apb_addr;
    assign apb_addr = apbAddrSt'(apbReg.paddr) & 32'h1ff;
    // Register/memory address offsets for decode documentation
    localparam int unsigned REG_BLOCKB_BLOCKBTABLE1 = 32'h00000000; // Dual Port with one connection
    localparam int unsigned REG_BLOCKB_BLOCKBTABLE1_SIZE = 32'h00000050; // Decode range size
    localparam int unsigned REG_BLOCKB_BLOCKBTABLE37BIT = 32'h00000080; // External 37-bit memory register - firmware accessible with 8-byte stride
    localparam int unsigned REG_BLOCKB_BLOCKBTABLE37BIT_SIZE = 32'h00000050; // Decode range size
    localparam int unsigned REG_BLOCKB_BLOCKBTABLEEXT = 32'h00000100; // Memory register - firmware accessible memory-mapped storage
    localparam int unsigned REG_BLOCKB_BLOCKBTABLEEXT_SIZE = 32'h00000028; // Decode range size
    localparam int unsigned REG_BLOCKB_RWARR = 32'h00000140; // A Read Write register array
    localparam int unsigned REG_BLOCKB_RWARR_STRIDE = 32'h00000008; // rwArr element stride
    localparam int unsigned REG_BLOCKB_RWARR_0 = REG_BLOCKB_RWARR + 0 * REG_BLOCKB_RWARR_STRIDE; // rwArr[0]
    localparam int unsigned REG_BLOCKB_RWARR_1 = REG_BLOCKB_RWARR + 1 * REG_BLOCKB_RWARR_STRIDE; // rwArr[1]
    localparam int unsigned REG_BLOCKB_RWARR_2 = REG_BLOCKB_RWARR + 2 * REG_BLOCKB_RWARR_STRIDE; // rwArr[2]
    localparam int unsigned REG_BLOCKB_RWARR_3 = REG_BLOCKB_RWARR + 3 * REG_BLOCKB_RWARR_STRIDE; // rwArr[3]
    localparam int unsigned REG_BLOCKB_EXTARR = 32'h00000160; // An External register array
    localparam int unsigned REG_BLOCKB_EXTARR_STRIDE = 32'h00000008; // extArr element stride
    localparam int unsigned REG_BLOCKB_EXTARR_0 = REG_BLOCKB_EXTARR + 0 * REG_BLOCKB_EXTARR_STRIDE; // extArr[0]
    localparam int unsigned REG_BLOCKB_EXTARR_1 = REG_BLOCKB_EXTARR + 1 * REG_BLOCKB_EXTARR_STRIDE; // extArr[1]
    localparam int unsigned REG_BLOCKB_EXTARR_2 = REG_BLOCKB_EXTARR + 2 * REG_BLOCKB_EXTARR_STRIDE; // extArr[2]
    localparam int unsigned REG_BLOCKB_EXTARR_3 = REG_BLOCKB_EXTARR + 3 * REG_BLOCKB_EXTARR_STRIDE; // extArr[3]
    localparam int unsigned REG_BLOCKB_RWD = 32'h00000180; // A Read Write register
    localparam int unsigned REG_BLOCKB_ROBSIZE = 32'h00000188; // A Read Only register with a structure that has a definition from an included context

    dRegSt rwD_reg;
    logic rwD_reg_update_0;
    assign rwD.data = rwD_reg;
    `DFFREN_DOM(clk, rst_n, rwD_reg[6:0], apbReg.pwdata[6:0], rwD_reg_update_0, 7'h00000000)

    bSizeRegSt roBsize_reg;
    assign roBsize_reg = roBsize.data;

    dRegSt rwArr_0_reg;
    logic rwArr_0_reg_update_0;
    assign rwArr[0].data = rwArr_0_reg;
    `DFFREN_DOM(clk, rst_n, rwArr_0_reg[6:0], apbReg.pwdata[6:0], rwArr_0_reg_update_0, 7'h00000000)

    dRegSt rwArr_1_reg;
    logic rwArr_1_reg_update_0;
    assign rwArr[1].data = rwArr_1_reg;
    `DFFREN_DOM(clk, rst_n, rwArr_1_reg[6:0], apbReg.pwdata[6:0], rwArr_1_reg_update_0, 7'h00000000)

    dRegSt rwArr_2_reg;
    logic rwArr_2_reg_update_0;
    assign rwArr[2].data = rwArr_2_reg;
    `DFFREN_DOM(clk, rst_n, rwArr_2_reg[6:0], apbReg.pwdata[6:0], rwArr_2_reg_update_0, 7'h00000000)

    dRegSt rwArr_3_reg;
    logic rwArr_3_reg_update_0;
    assign rwArr[3].data = rwArr_3_reg;
    `DFFREN_DOM(clk, rst_n, rwArr_3_reg[6:0], apbReg.pwdata[6:0], rwArr_3_reg_update_0, 7'h00000000)

    dRegSt extArr_0_reg;
    assign extArr_0_reg = extArr[0].rdata;

    dRegSt extArr_1_reg;
    assign extArr_1_reg = extArr[1].rdata;

    dRegSt extArr_2_reg;
    assign extArr_2_reg = extArr[2].rdata;

    dRegSt extArr_3_reg;
    assign extArr_3_reg = extArr[3].rdata;

    // blockBTable1
    bigSt nxt_blockBTable1_data, blockBTable1_data;
    bSizeSt blockBTable1_addr;

    logic blockBTable1_update_0;
    logic blockBTable1_update_1;
    logic nxt_blockBTable1_rd_enable, blockBTable1_rd_enable, blockBTable1_rd_capture;
    logic blockBTable1_wr_enable;

    `DFF_DOM(clk, rst_n, blockBTable1_addr, bSizeSt'((apb_addr - REG_BLOCKB_BLOCKBTABLE1) >> 3))
    `DFF_DOM(clk, rst_n, blockBTable1_wr_enable, blockBTable1_update_1)
    `DFF_DOM(clk, rst_n, blockBTable1_rd_enable, nxt_blockBTable1_rd_enable)
    `DFF_DOM(clk, rst_n, blockBTable1_rd_capture, blockBTable1_rd_enable)

    `DFFEN_DOM(clk, rst_n, blockBTable1_data[31:0], nxt_blockBTable1_data[31:0], blockBTable1_update_0)
    `DFFEN_DOM(clk, rst_n, blockBTable1_data[63:32], nxt_blockBTable1_data[63:32], blockBTable1_update_1)

    assign blockBTable1.enable      = blockBTable1_rd_enable | blockBTable1_wr_enable;
    assign blockBTable1.wr_en       = blockBTable1_wr_enable;
    assign blockBTable1.addr        = blockBTable1_addr;
    assign blockBTable1.write_data  = blockBTable1_data;

    // blockBTableExt
    seeSt nxt_blockBTableExt_data, blockBTableExt_data;
    bSizeSt blockBTableExt_addr;

    logic blockBTableExt_update_0;
    logic nxt_blockBTableExt_rd_enable, blockBTableExt_rd_enable, blockBTableExt_rd_capture;
    logic blockBTableExt_wr_enable;

    `DFF_DOM(clk, rst_n, blockBTableExt_addr, bSizeSt'((apb_addr - REG_BLOCKB_BLOCKBTABLEEXT) >> 2))
    `DFF_DOM(clk, rst_n, blockBTableExt_wr_enable, blockBTableExt_update_0)
    `DFF_DOM(clk, rst_n, blockBTableExt_rd_enable, nxt_blockBTableExt_rd_enable)
    `DFF_DOM(clk, rst_n, blockBTableExt_rd_capture, blockBTableExt_rd_enable)

    `DFFEN_DOM(clk, rst_n, blockBTableExt_data[4:0], nxt_blockBTableExt_data[4:0], blockBTableExt_update_0)

    assign blockBTableExt.enable      = blockBTableExt_rd_enable | blockBTableExt_wr_enable;
    assign blockBTableExt.wr_en       = blockBTableExt_wr_enable;
    assign blockBTableExt.addr        = blockBTableExt_addr;
    assign blockBTableExt.write_data  = blockBTableExt_data;

    // blockBTable37Bit
    test37BitRegSt nxt_blockBTable37Bit_data, blockBTable37Bit_data;
    bSizeSt blockBTable37Bit_addr;

    logic blockBTable37Bit_update_0;
    logic blockBTable37Bit_update_1;
    logic nxt_blockBTable37Bit_rd_enable, blockBTable37Bit_rd_enable, blockBTable37Bit_rd_capture;
    logic blockBTable37Bit_wr_enable;

    `DFF_DOM(clk, rst_n, blockBTable37Bit_addr, bSizeSt'((apb_addr - REG_BLOCKB_BLOCKBTABLE37BIT) >> 3))
    `DFF_DOM(clk, rst_n, blockBTable37Bit_wr_enable, blockBTable37Bit_update_1)
    `DFF_DOM(clk, rst_n, blockBTable37Bit_rd_enable, nxt_blockBTable37Bit_rd_enable)
    `DFF_DOM(clk, rst_n, blockBTable37Bit_rd_capture, blockBTable37Bit_rd_enable)

    `DFFEN_DOM(clk, rst_n, blockBTable37Bit_data[31:0], nxt_blockBTable37Bit_data[31:0], blockBTable37Bit_update_0)
    `DFFEN_DOM(clk, rst_n, blockBTable37Bit_data[36:32], nxt_blockBTable37Bit_data[36:32], blockBTable37Bit_update_1)

    assign blockBTable37Bit.enable      = blockBTable37Bit_rd_enable | blockBTable37Bit_wr_enable;
    assign blockBTable37Bit.wr_en       = blockBTable37Bit_wr_enable;
    assign blockBTable37Bit.addr        = blockBTable37Bit_addr;
    assign blockBTable37Bit.write_data  = blockBTable37Bit_data;

    logic wr_select;
    logic rd_select;
    assign wr_select = apbReg.psel & apbReg.penable & apbReg.pwrite & rst_n;
    assign rd_select = apbReg.psel & apbReg.penable & !apbReg.pwrite & rst_n;

    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_ready = 1'b0;
        rwD_reg_update_0 = 1'b0;
        rwArr_0_reg_update_0 = 1'b0;
        rwArr_1_reg_update_0 = 1'b0;
        rwArr_2_reg_update_0 = 1'b0;
        rwArr_3_reg_update_0 = 1'b0;
        extArr[0].write = '0;
        extArr[0].wdata = '0;
        extArr[1].write = '0;
        extArr[1].wdata = '0;
        extArr[2].write = '0;
        extArr[2].wdata = '0;
        extArr[3].write = '0;
        extArr[3].wdata = '0;
        blockBTable1_update_0 = 1'b0;
        blockBTable1_update_1 = 1'b0;
        nxt_blockBTable1_data = blockBTable1_data;
        blockBTableExt_update_0 = 1'b0;
        nxt_blockBTableExt_data = blockBTableExt_data;
        blockBTable37Bit_update_0 = 1'b0;
        blockBTable37Bit_update_1 = 1'b0;
        nxt_blockBTable37Bit_data = blockBTable37Bit_data;
        if (wr_select) begin
            case (apb_addr) inside
                REG_BLOCKB_RWD : begin
                    rwD_reg_update_0 = 1'b1;
                end
                REG_BLOCKB_RWARR_0 : begin
                    rwArr_0_reg_update_0 = 1'b1;
                end
                REG_BLOCKB_RWARR_1 : begin
                    rwArr_1_reg_update_0 = 1'b1;
                end
                REG_BLOCKB_RWARR_2 : begin
                    rwArr_2_reg_update_0 = 1'b1;
                end
                REG_BLOCKB_RWARR_3 : begin
                    rwArr_3_reg_update_0 = 1'b1;
                end
                REG_BLOCKB_EXTARR_0 : begin
                    extArr[0].write = 1;
                    extArr[0].wdata[6:0] = apbReg.pwdata[6:0];
                end
                REG_BLOCKB_EXTARR_1 : begin
                    extArr[1].write = 1;
                    extArr[1].wdata[6:0] = apbReg.pwdata[6:0];
                end
                REG_BLOCKB_EXTARR_2 : begin
                    extArr[2].write = 1;
                    extArr[2].wdata[6:0] = apbReg.pwdata[6:0];
                end
                REG_BLOCKB_EXTARR_3 : begin
                    extArr[3].write = 1;
                    extArr[3].wdata[6:0] = apbReg.pwdata[6:0];
                end
                [REG_BLOCKB_BLOCKBTABLE1:REG_BLOCKB_BLOCKBTABLE1 + REG_BLOCKB_BLOCKBTABLE1_SIZE - 32'd4]: begin
                    case (3'(apb_addr - REG_BLOCKB_BLOCKBTABLE1))
                        3'h0: begin
                            blockBTable1_update_0 = 1'b1;
                            nxt_blockBTable1_data[31:0] = apbReg.pwdata[31:0];
                        end
                        3'h4: begin
                            blockBTable1_update_1 = 1'b1;
                            nxt_blockBTable1_data[63:32] = apbReg.pwdata[31:0];
                        end
                        default: ;
                    endcase
                end
                [REG_BLOCKB_BLOCKBTABLEEXT:REG_BLOCKB_BLOCKBTABLEEXT + REG_BLOCKB_BLOCKBTABLEEXT_SIZE - 32'd4]: begin
                    case (2'(apb_addr - REG_BLOCKB_BLOCKBTABLEEXT))
                        2'h0: begin
                            blockBTableExt_update_0 = 1'b1;
                            nxt_blockBTableExt_data[4:0] = apbReg.pwdata[4:0];
                        end
                        default: ;
                    endcase
                end
                [REG_BLOCKB_BLOCKBTABLE37BIT:REG_BLOCKB_BLOCKBTABLE37BIT + REG_BLOCKB_BLOCKBTABLE37BIT_SIZE - 32'd4]: begin
                    case (3'(apb_addr - REG_BLOCKB_BLOCKBTABLE37BIT))
                        3'h0: begin
                            blockBTable37Bit_update_0 = 1'b1;
                            nxt_blockBTable37Bit_data[31:0] = apbReg.pwdata[31:0];
                        end
                        3'h4: begin
                            blockBTable37Bit_update_1 = 1'b1;
                            nxt_blockBTable37Bit_data[36:32] = apbReg.pwdata[4:0];
                        end
                        default: ;
                    endcase
                end
                default: ; // unmapped/ro write: silently ignored (ACK below)
            endcase
            nxt_wr_ready = 1'b1;
        end
    end

    logic nxt_rd_ready, rd_ready;
    apbDataSt nxt_rd_data, rd_data;
    always_comb begin
        nxt_rd_ready = 1'b0;
        nxt_rd_data = '0;
        nxt_blockBTable1_rd_enable = 1'b0;
        nxt_blockBTableExt_rd_enable = 1'b0;
        nxt_blockBTable37Bit_rd_enable = 1'b0;
        if (rd_select) begin
            case (apb_addr) inside
                REG_BLOCKB_RWD : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(rwD_reg[6:0]);
                end
                REG_BLOCKB_ROBSIZE : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(roBsize_reg[3:0]);
                end
                REG_BLOCKB_RWARR_0 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(rwArr_0_reg[6:0]);
                end
                REG_BLOCKB_RWARR_1 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(rwArr_1_reg[6:0]);
                end
                REG_BLOCKB_RWARR_2 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(rwArr_2_reg[6:0]);
                end
                REG_BLOCKB_RWARR_3 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(rwArr_3_reg[6:0]);
                end
                REG_BLOCKB_EXTARR_0 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(extArr_0_reg[6:0]);
                end
                REG_BLOCKB_EXTARR_1 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(extArr_1_reg[6:0]);
                end
                REG_BLOCKB_EXTARR_2 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(extArr_2_reg[6:0]);
                end
                REG_BLOCKB_EXTARR_3 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(extArr_3_reg[6:0]);
                end
                [REG_BLOCKB_BLOCKBTABLE1:REG_BLOCKB_BLOCKBTABLE1 + REG_BLOCKB_BLOCKBTABLE1_SIZE - 32'd4]: begin
                    case (3'(apb_addr - REG_BLOCKB_BLOCKBTABLE1))
                        3'h0: begin
                            if (blockBTable1_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockBTable1.read_data[31:0]);
                            end
                        end
                        3'h4: begin
                            if (blockBTable1_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockBTable1.read_data[63:32]);
                            end
                        end
                        default: begin
                            nxt_rd_ready = 1'b1;
                            nxt_rd_data = '0;
                        end
                    endcase
                    nxt_blockBTable1_rd_enable = (3'(apb_addr - REG_BLOCKB_BLOCKBTABLE1) inside {3'h0, 3'h4}) & ~blockBTable1_rd_capture;
                end
                [REG_BLOCKB_BLOCKBTABLEEXT:REG_BLOCKB_BLOCKBTABLEEXT + REG_BLOCKB_BLOCKBTABLEEXT_SIZE - 32'd4]: begin
                    case (2'(apb_addr - REG_BLOCKB_BLOCKBTABLEEXT))
                        2'h0: begin
                            if (blockBTableExt_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockBTableExt.read_data[4:0]);
                            end
                        end
                        default: begin
                            nxt_rd_ready = 1'b1;
                            nxt_rd_data = '0;
                        end
                    endcase
                    nxt_blockBTableExt_rd_enable = (2'(apb_addr - REG_BLOCKB_BLOCKBTABLEEXT) inside {2'h0}) & ~blockBTableExt_rd_capture;
                end
                [REG_BLOCKB_BLOCKBTABLE37BIT:REG_BLOCKB_BLOCKBTABLE37BIT + REG_BLOCKB_BLOCKBTABLE37BIT_SIZE - 32'd4]: begin
                    case (3'(apb_addr - REG_BLOCKB_BLOCKBTABLE37BIT))
                        3'h0: begin
                            if (blockBTable37Bit_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockBTable37Bit.read_data[31:0]);
                            end
                        end
                        3'h4: begin
                            if (blockBTable37Bit_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockBTable37Bit.read_data[36:32]);
                            end
                        end
                        default: begin
                            nxt_rd_ready = 1'b1;
                            nxt_rd_data = '0;
                        end
                    endcase
                    nxt_blockBTable37Bit_rd_enable = (3'(apb_addr - REG_BLOCKB_BLOCKBTABLE37BIT) inside {3'h0, 3'h4}) & ~blockBTable37Bit_rd_capture;
                end
                default: begin // unmapped read: ACK with 32'hBADD_C0DE (never stall, never error)
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(32'hBADD_C0DE);
                end
            endcase
        end
    end

    // Update APB ready and read data. The bus is never stalled and slave
    // error is never asserted: every access ACKs, unmapped reads return
    // 32'hBADD_C0DE.
    generate if (APB_READY_1WS)
        begin
            `DFFR_DOM(clk, rst_n, wr_ready,   nxt_wr_ready,   '0)
            `DFFR_DOM(clk, rst_n, rd_ready,   nxt_rd_ready,   '0)
            `DFFR_DOM(clk, rst_n, rd_data,    nxt_rd_data,    '0)
        end else begin
            assign wr_ready   = nxt_wr_ready;
            assign rd_ready   = nxt_rd_ready;
            assign rd_data    = nxt_rd_data;
        end
    endgenerate

    // Update the APB interface
    assign apbReg.prdata  = rd_data;
    assign apbReg.pready  = rd_ready | wr_ready;
    assign apbReg.pslverr = 1'b0;

endmodule : blockBRegs
// GENERATED_CODE_END
