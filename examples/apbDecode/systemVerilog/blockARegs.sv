// GENERATED_CODE_PARAM --block=blockARegs
// GENERATED_CODE_BEGIN --template=moduleRegs
module blockARegs
    // Generated Import package statement(s)
    import apbDecode_package::*;

    #(
        parameter apbAddrSt APB_ADDR_MASK = '1,
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst apbReg,
        status_if.dst roA,
        status_if.src rwUn0A,
        status_if.dst roUn0A,
        external_reg_if.src extA,
        memory_if.src blockATable0,
        memory_if.src blockATable1,
        input clk,
        input rst_n
    );

    apbAddrSt apb_addr;
    assign apb_addr = apbAddrSt'(apbReg.paddr) & APB_ADDR_MASK;

    aRegSt roA_reg;
    assign roA_reg = roA.data;

    un0ARegSt rwUn0A_reg;
    logic rwUn0A_reg_update_0;
    logic rwUn0A_reg_update_1;
    assign rwUn0A.data = rwUn0A_reg;
    `DFFEN(rwUn0A_reg[31:0], apbReg.pwdata[31:0], rwUn0A_reg_update_0)
    `DFFEN(rwUn0A_reg[47:32], apbReg.pwdata[15:0], rwUn0A_reg_update_1)

    un0ARegSt roUn0A_reg;
    assign roUn0A_reg = roUn0A.data;

    un0ARegSt extA_reg;
    assign extA_reg = extA.rdata;

    // blockATable0
    aMemSt nxt_blockATable0_data, blockATable0_data;
    aMemAddrSt blockATable0_addr;

    logic blockATable0_update_0;
    logic blockATable0_update_1;
    logic nxt_blockATable0_rd_enable, blockATable0_rd_enable, blockATable0_rd_capture;
    logic blockATable0_wr_enable;

    `DFF(blockATable0_addr, aMemAddrSt'(apb_addr[31:3]))
    `DFF(blockATable0_wr_enable, blockATable0_update_1)
    `DFF(blockATable0_rd_enable, nxt_blockATable0_rd_enable)
    `DFF(blockATable0_rd_capture, blockATable0_rd_enable)

    `DFFEN(blockATable0_data[31:0], nxt_blockATable0_data[31:0], blockATable0_update_0)
    `DFFEN(blockATable0_data[62:32], nxt_blockATable0_data[62:32], blockATable0_update_1)

    assign blockATable0.enable      = blockATable0_rd_enable | blockATable0_wr_enable;
    assign blockATable0.wr_en       = blockATable0_wr_enable;
    assign blockATable0.addr        = blockATable0_addr;
    assign blockATable0.write_data  = blockATable0_data;

    // blockATable1
    aMemSt nxt_blockATable1_data, blockATable1_data;
    aMemAddrSt blockATable1_addr;

    logic blockATable1_update_0;
    logic blockATable1_update_1;
    logic nxt_blockATable1_rd_enable, blockATable1_rd_enable, blockATable1_rd_capture;
    logic blockATable1_wr_enable;

    `DFF(blockATable1_addr, aMemAddrSt'(apb_addr[31:3]))
    `DFF(blockATable1_wr_enable, blockATable1_update_1)
    `DFF(blockATable1_rd_enable, nxt_blockATable1_rd_enable)
    `DFF(blockATable1_rd_capture, blockATable1_rd_enable)

    `DFFEN(blockATable1_data[31:0], nxt_blockATable1_data[31:0], blockATable1_update_0)
    `DFFEN(blockATable1_data[62:32], nxt_blockATable1_data[62:32], blockATable1_update_1)

    assign blockATable1.enable      = blockATable1_rd_enable | blockATable1_wr_enable;
    assign blockATable1.wr_en       = blockATable1_wr_enable;
    assign blockATable1.addr        = blockATable1_addr;
    assign blockATable1.write_data  = blockATable1_data;

    logic wr_select;
    logic rd_select;
    assign wr_select = apbReg.psel & apbReg.penable & apbReg.pwrite & rst_n;
    assign rd_select = apbReg.psel & apbReg.penable & !apbReg.pwrite & rst_n;

    logic nxt_wr_pslverr, wr_pslverr;
    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_pslverr = 1'b0;
        nxt_wr_ready = 1'b0;
        rwUn0A_reg_update_0 = 1'b0;
        rwUn0A_reg_update_1 = 1'b0;
        extA.write = '0;
        extA.wdata = '0;
        blockATable0_update_0 = 1'b0;
        blockATable0_update_1 = 1'b0;
        nxt_blockATable0_data = blockATable0_data;
        blockATable1_update_0 = 1'b0;
        blockATable1_update_1 = 1'b0;
        nxt_blockATable1_data = blockATable1_data;
        if (wr_select) begin
            case (apb_addr) inside
                32'h208 : begin
                    rwUn0A_reg_update_0 = 1'b1;
                end
                32'h20c : begin
                    rwUn0A_reg_update_1 = 1'b1;
                end
                32'h218 : begin
                    extA.write = 1;
                    extA.wdata[31:0] = apbReg.pwdata[31:0];
                    extA.wdata[47:32] = extA.rdata[47:32];
                end
                32'h21c : begin
                    extA.write = 2;
                    extA.wdata[31:0] = extA.rdata[31:0];
                    extA.wdata[47:32] = apbReg.pwdata[15:0];
                end
                [32'h0:32'h94]: begin
                    case (apb_addr[2:0])
                        3'h0: begin
                            blockATable0_update_0 = 1'b1;
                            nxt_blockATable0_data[31:0] = apbReg.pwdata[31:0];
                        end
                        3'h4: begin
                            blockATable0_update_1 = 1'b1;
                            nxt_blockATable0_data[62:32] = apbReg.pwdata[30:0];
                        end
                        default: ;
                    endcase
                end
                [32'h100:32'h194]: begin
                    case (apb_addr[2:0])
                        3'h0: begin
                            blockATable1_update_0 = 1'b1;
                            nxt_blockATable1_data[31:0] = apbReg.pwdata[31:0];
                        end
                        3'h4: begin
                            blockATable1_update_1 = 1'b1;
                            nxt_blockATable1_data[62:32] = apbReg.pwdata[30:0];
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
        nxt_blockATable0_rd_enable = 1'b0;
        nxt_blockATable1_rd_enable = 1'b0;
        if (rd_select) begin
            case (apb_addr) inside
                32'h200 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(roA_reg[31:0]);
                end
                32'h204 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(roA_reg[36:32]);
                end
                32'h208 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(rwUn0A_reg[31:0]);
                end
                32'h20c : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(rwUn0A_reg[47:32]);
                end
                32'h210 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(roUn0A_reg[31:0]);
                end
                32'h214 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(roUn0A_reg[47:32]);
                end
                32'h218 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(extA_reg[31:0]);
                end
                32'h21c : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(extA_reg[47:32]);
                end
                [32'h0:32'h94]: begin
                    case (apb_addr[2:0])
                        3'h0: begin
                            if (blockATable0_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockATable0.read_data[31:0]);
                            end
                        end
                        3'h4: begin
                            if (blockATable0_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockATable0.read_data[62:32]);
                            end
                        end
                        default: ;
                    endcase
                    nxt_blockATable0_rd_enable = ~blockATable0_rd_capture;
                end
                [32'h100:32'h194]: begin
                    case (apb_addr[2:0])
                        3'h0: begin
                            if (blockATable1_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockATable1.read_data[31:0]);
                            end
                        end
                        3'h4: begin
                            if (blockATable1_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(blockATable1.read_data[62:32]);
                            end
                        end
                        default: ;
                    endcase
                    nxt_blockATable1_rd_enable = ~blockATable1_rd_capture;
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
