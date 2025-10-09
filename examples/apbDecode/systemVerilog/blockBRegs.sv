// GENERATED_CODE_PARAM --block=blockBRegs
// GENERATED_CODE_BEGIN --template=moduleRegs
module blockBRegs
    // Generated Import package statement(s)
    import apbDecode_package::*;
    #(
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst apbReg,
        status_if.src rwUn0B,
        status_if.dst roB,
        memory_if.src blockBTable,
        input clk,
        input rst_n
    );

    apbAddrSt apb_addr;
    assign apb_addr = apbAddrSt'(apbReg.paddr) & 32'h3ff;

    un0BRegSt rwUn0B_reg;
    logic rwUn0B_reg_update_0;
    assign rwUn0B.data = rwUn0B_reg;
    `DFFEN(rwUn0B_reg[23:0], apbReg.pwdata[23:0], rwUn0B_reg_update_0)

    aSizeRegSt roB_reg;
    assign roB_reg = roB.data;

    // blockBTable
    bMemSt nxt_blockBTable_data, blockBTable_data;
    bMemAddrSt blockBTable_addr;

    logic blockBTable_update_0;
    logic blockBTable_update_1;
    logic blockBTable_update_2;
    logic nxt_blockBTable_rd_enable, blockBTable_rd_enable, blockBTable_rd_capture;
    logic blockBTable_wr_enable;

    `DFF(blockBTable_addr, bMemAddrSt'(apb_addr[31:4]))
    `DFF(blockBTable_wr_enable, blockBTable_update_2)
    `DFF(blockBTable_rd_enable, nxt_blockBTable_rd_enable)
    `DFF(blockBTable_rd_capture, blockBTable_rd_enable)

    `DFFEN(blockBTable_data[31:0], nxt_blockBTable_data[31:0], blockBTable_update_0)
    `DFFEN(blockBTable_data[63:32], nxt_blockBTable_data[63:32], blockBTable_update_1)
    `DFFEN(blockBTable_data[95:64], nxt_blockBTable_data[95:64], blockBTable_update_2)

    assign blockBTable.enable      = blockBTable_rd_enable | blockBTable_wr_enable;
    assign blockBTable.wr_en       = blockBTable_wr_enable;
    assign blockBTable.addr        = blockBTable_addr;
    assign blockBTable.write_data  = blockBTable_data;

    logic wr_select;
    logic rd_select;
    assign wr_select = apbReg.psel & apbReg.penable & apbReg.pwrite & rst_n;
    assign rd_select = apbReg.psel & apbReg.penable & !apbReg.pwrite & rst_n;

    logic nxt_wr_pslverr, wr_pslverr;
    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_pslverr = 1'b0;
        nxt_wr_ready = 1'b0;
        rwUn0B_reg_update_0 = 1'b0;
        blockBTable_update_0 = 1'b0;
        blockBTable_update_1 = 1'b0;
        blockBTable_update_2 = 1'b0;
        nxt_blockBTable_data = blockBTable_data;
        if (wr_select) begin
            case (apb_addr) inside
                32'h200 : begin
                    rwUn0B_reg_update_0 = 1'b1;
                end
                [32'h0:32'h14c]: begin
                    case (apb_addr[3:0])
                        4'h0: begin
                            blockBTable_update_0 = 1'b1;
                            nxt_blockBTable_data[31:0] = apbReg.pwdata[31:0];
                        end
                        4'h4: begin
                            blockBTable_update_1 = 1'b1;
                            nxt_blockBTable_data[63:32] = apbReg.pwdata[31:0];
                        end
                        4'h8: begin
                            blockBTable_update_2 = 1'b1;
                            nxt_blockBTable_data[95:64] = apbReg.pwdata[31:0];
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
        nxt_blockBTable_rd_enable = 1'b0;
        if (rd_select) begin
            case (apb_addr) inside
                32'h200 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(rwUn0B_reg[23:0]);
                end
                32'h208 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(roB_reg[28:0]);
                end
                [32'h0:32'h14c]: begin
                    case (apb_addr[3:0])
                        4'h0: begin
                            if (blockBTable_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockBTable.read_data[31:0]);
                            end
                        end
                        4'h4: begin
                            if (blockBTable_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockBTable.read_data[63:32]);
                            end
                        end
                        4'h8: begin
                            if (blockBTable_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockBTable.read_data[95:64]);
                            end
                        end
                        default: ;
                    endcase
                    nxt_blockBTable_rd_enable = ~blockBTable_rd_capture;
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
