// GENERATED_CODE_PARAM --block=blockARegs
// GENERATED_CODE_BEGIN --template=moduleRegs
module blockARegs
    // Generated Import package statement(s)
    import mixedInclude_package::*;
    import mixed_package::*;
    #(
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst apbReg,
        status_if.dst roA,
        memory_if.src blockATableLocal,
        memory_if.src blockATable37Bit,
        input clk,
        input rst_n
    );

    apbAddrSt apb_addr;
    assign apb_addr = apbAddrSt'(apbReg.paddr) & 32'h7f;

    aRegSt roA_reg;
    assign roA_reg = roA.data;

    // blockATableLocal
    aRegSt nxt_blockATableLocal_data, blockATableLocal_data;
    bSizeSt blockATableLocal_addr;

    logic blockATableLocal_update_0;
    logic nxt_blockATableLocal_rd_enable, blockATableLocal_rd_enable, blockATableLocal_rd_capture;
    logic blockATableLocal_wr_enable;

    `DFF(blockATableLocal_addr, bSizeSt'(apb_addr[31:2]))
    `DFF(blockATableLocal_wr_enable, blockATableLocal_update_0)
    `DFF(blockATableLocal_rd_enable, nxt_blockATableLocal_rd_enable)
    `DFF(blockATableLocal_rd_capture, blockATableLocal_rd_enable)

    `DFFEN(blockATableLocal_data[6:0], nxt_blockATableLocal_data[6:0], blockATableLocal_update_0)

    assign blockATableLocal.enable      = blockATableLocal_rd_enable | blockATableLocal_wr_enable;
    assign blockATableLocal.wr_en       = blockATableLocal_wr_enable;
    assign blockATableLocal.addr        = blockATableLocal_addr;
    assign blockATableLocal.write_data  = blockATableLocal_data;

    // blockATable37Bit
    test37BitRegSt nxt_blockATable37Bit_data, blockATable37Bit_data;
    bSizeSt blockATable37Bit_addr;

    logic blockATable37Bit_update_0;
    logic blockATable37Bit_update_1;
    logic nxt_blockATable37Bit_rd_enable, blockATable37Bit_rd_enable, blockATable37Bit_rd_capture;
    logic blockATable37Bit_wr_enable;

    `DFF(blockATable37Bit_addr, bSizeSt'(apb_addr[31:3]))
    `DFF(blockATable37Bit_wr_enable, blockATable37Bit_update_1)
    `DFF(blockATable37Bit_rd_enable, nxt_blockATable37Bit_rd_enable)
    `DFF(blockATable37Bit_rd_capture, blockATable37Bit_rd_enable)

    `DFFEN(blockATable37Bit_data[31:0], nxt_blockATable37Bit_data[31:0], blockATable37Bit_update_0)
    `DFFEN(blockATable37Bit_data[36:32], nxt_blockATable37Bit_data[36:32], blockATable37Bit_update_1)

    assign blockATable37Bit.enable      = blockATable37Bit_rd_enable | blockATable37Bit_wr_enable;
    assign blockATable37Bit.wr_en       = blockATable37Bit_wr_enable;
    assign blockATable37Bit.addr        = blockATable37Bit_addr;
    assign blockATable37Bit.write_data  = blockATable37Bit_data;

    logic wr_select;
    logic rd_select;
    assign wr_select = apbReg.psel & apbReg.penable & apbReg.pwrite & rst_n;
    assign rd_select = apbReg.psel & apbReg.penable & !apbReg.pwrite & rst_n;

    logic nxt_wr_pslverr, wr_pslverr;
    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_pslverr = 1'b0;
        nxt_wr_ready = 1'b0;
        blockATableLocal_update_0 = 1'b0;
        nxt_blockATableLocal_data = blockATableLocal_data;
        blockATable37Bit_update_0 = 1'b0;
        blockATable37Bit_update_1 = 1'b0;
        nxt_blockATable37Bit_data = blockATable37Bit_data;
        if (wr_select) begin
            case (apb_addr) inside
                [32'h50:32'h74]: begin
                    case (apb_addr[2-1:0])
                        2'h0: begin
                            blockATableLocal_update_0 = 1'b1;
                            nxt_blockATableLocal_data[6:0] = apbReg.pwdata[6:0];
                        end
                        default: ;
                    endcase
                end
                [32'h0:32'h4c]: begin
                    case (apb_addr[3-1:0])
                        3'h0: begin
                            blockATable37Bit_update_0 = 1'b1;
                            nxt_blockATable37Bit_data[31:0] = apbReg.pwdata[31:0];
                        end
                        3'h4: begin
                            blockATable37Bit_update_1 = 1'b1;
                            nxt_blockATable37Bit_data[36:32] = apbReg.pwdata[4:0];
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
        nxt_blockATableLocal_rd_enable = 1'b0;
        nxt_blockATable37Bit_rd_enable = 1'b0;
        if (rd_select) begin
            case (apb_addr) inside
                32'h78 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(roA_reg[6:0]);
                end
                [32'h50:32'h74]: begin
                    case (apb_addr[2-1:0])
                        2'h0: begin
                            if (blockATableLocal_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockATableLocal.read_data[6:0]);
                            end
                        end
                        default: ;
                    endcase
                    nxt_blockATableLocal_rd_enable = ~blockATableLocal_rd_capture;
                end
                [32'h0:32'h4c]: begin
                    case (apb_addr[3-1:0])
                        3'h0: begin
                            if (blockATable37Bit_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockATable37Bit.read_data[31:0]);
                            end
                        end
                        3'h4: begin
                            if (blockATable37Bit_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockATable37Bit.read_data[36:32]);
                            end
                        end
                        default: ;
                    endcase
                    nxt_blockATable37Bit_rd_enable = ~blockATable37Bit_rd_capture;
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

endmodule : blockARegs
// GENERATED_CODE_END
