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
        memory_if.src blockBTable1,
        input clk,
        input rst_n
    );

    apbAddrSt apb_addr;
    assign apb_addr = apbAddrSt'(apbReg.paddr) & 32'hff;

    dRegSt rwD_reg;
    logic rwD_reg_update_0;
    assign rwD.data = rwD_reg;
    `DFFREN(rwD_reg[6:0], apbReg.pwdata[6:0], rwD_reg_update_0, 7'h00000000)

    bSizeRegSt roBsize_reg;
    assign roBsize_reg = roBsize.data;

    // blockBTable1
    bigSt nxt_blockBTable1_data, blockBTable1_data;
    bSizeSt blockBTable1_addr;

    logic blockBTable1_update_0;
    logic blockBTable1_update_1;
    logic nxt_blockBTable1_rd_enable, blockBTable1_rd_enable, blockBTable1_rd_capture;
    logic blockBTable1_wr_enable;

    `DFF(blockBTable1_addr, bSizeSt'(apb_addr[31:3]))
    `DFF(blockBTable1_wr_enable, blockBTable1_update_1)
    `DFF(blockBTable1_rd_enable, nxt_blockBTable1_rd_enable)
    `DFF(blockBTable1_rd_capture, blockBTable1_rd_enable)

    `DFFEN(blockBTable1_data[31:0], nxt_blockBTable1_data[31:0], blockBTable1_update_0)
    `DFFEN(blockBTable1_data[63:32], nxt_blockBTable1_data[63:32], blockBTable1_update_1)

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

    `DFF(blockBTableExt_addr, bSizeSt'(apb_addr[31:2]))
    `DFF(blockBTableExt_wr_enable, blockBTableExt_update_0)
    `DFF(blockBTableExt_rd_enable, nxt_blockBTableExt_rd_enable)
    `DFF(blockBTableExt_rd_capture, blockBTableExt_rd_enable)

    `DFFEN(blockBTableExt_data[4:0], nxt_blockBTableExt_data[4:0], blockBTableExt_update_0)

    assign blockBTableExt.enable      = blockBTableExt_rd_enable | blockBTableExt_wr_enable;
    assign blockBTableExt.wr_en       = blockBTableExt_wr_enable;
    assign blockBTableExt.addr        = blockBTableExt_addr;
    assign blockBTableExt.write_data  = blockBTableExt_data;

    logic wr_select;
    logic rd_select;
    assign wr_select = apbReg.psel & apbReg.penable & apbReg.pwrite & rst_n;
    assign rd_select = apbReg.psel & apbReg.penable & !apbReg.pwrite & rst_n;

    logic nxt_wr_pslverr, wr_pslverr;
    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_pslverr = 1'b0;
        nxt_wr_ready = 1'b0;
        rwD_reg_update_0 = 1'b0;
        blockBTable1_update_0 = 1'b0;
        blockBTable1_update_1 = 1'b0;
        nxt_blockBTable1_data = blockBTable1_data;
        blockBTableExt_update_0 = 1'b0;
        nxt_blockBTableExt_data = blockBTableExt_data;
        if (wr_select) begin
            case (apb_addr) inside
                32'ha8 : begin
                    rwD_reg_update_0 = 1'b1;
                end
                [32'h0:32'h4c]: begin
                    case (apb_addr[2:0])
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
                [32'h80:32'ha4]: begin
                    case (apb_addr[2-1:0])
                        2'h0: begin
                            blockBTableExt_update_0 = 1'b1;
                            nxt_blockBTableExt_data[4:0] = apbReg.pwdata[4:0];
                        end
                        default: ;
                    endcase
                end
                default: begin
                    nxt_wr_pslverr = 1'b1;
                end
            endcase
            nxt_wr_ready = 1'b1;
        end
    end

    logic nxt_rd_pslverr, rd_pslverr;
    logic nxt_rd_ready, rd_ready;
    apbDataSt nxt_rd_data, rd_data;
    always_comb begin
        nxt_rd_pslverr = 1'b0;
        nxt_rd_ready = 1'b0;
        nxt_rd_data = '0;
        nxt_blockBTable1_rd_enable = 1'b0;
        nxt_blockBTableExt_rd_enable = 1'b0;
        if (rd_select) begin
            case (apb_addr) inside
                32'ha8 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(rwD_reg[6:0]);
                end
                32'hb0 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(roBsize_reg[3:0]);
                end
                [32'h0:32'h4c]: begin
                    case (apb_addr[2:0])
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
                        default: ;
                    endcase
                    nxt_blockBTable1_rd_enable = ~blockBTable1_rd_capture;
                end
                [32'h80:32'ha4]: begin
                    case (apb_addr[2-1:0])
                        2'h0: begin
                            if (blockBTableExt_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockBTableExt.read_data[4:0]);
                            end
                        end
                        default: ;
                    endcase
                    nxt_blockBTableExt_rd_enable = ~blockBTableExt_rd_capture;
                end
                default: begin
                    nxt_rd_data = apbDataSt'(32'hBADD_C0DE);
                    nxt_rd_pslverr = 1'b1;
                end
            endcase
        end
    end

    // Update APB ready, pslverr, and read data
    generate if (APB_READY_1WS)
        begin
            `DFFR(wr_ready,   nxt_wr_ready,   '0)
            `DFFR(wr_pslverr, nxt_wr_pslverr, '0)
            `DFFR(rd_ready,   nxt_rd_ready,   '0)
            `DFFR(rd_data,    nxt_rd_data,    '0)
            `DFFR(rd_pslverr, nxt_rd_pslverr, '0)
        end else begin
            assign wr_ready   = nxt_wr_ready;
            assign wr_pslverr = nxt_wr_pslverr;
            assign rd_ready   = nxt_rd_ready;
            assign rd_data    = nxt_rd_data;
            assign rd_pslverr = nxt_rd_pslverr;
        end
    endgenerate

    // Update the APB interface
    assign apbReg.prdata  = rd_data;
    assign apbReg.pready  = rd_ready | wr_ready;
    assign apbReg.pslverr = rd_pslverr | wr_pslverr;

endmodule : blockBRegs
// GENERATED_CODE_END
