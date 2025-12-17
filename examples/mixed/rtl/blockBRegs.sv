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
        input clk,
        input rst_n
    );

    apbAddrSt apb_addr;
    assign apb_addr = apbAddrSt'(apbReg.paddr) & 32'hf;

    dRegSt rwD_reg;
    logic rwD_reg_update_0;
    assign rwD.data = rwD_reg;
    `DFFREN(rwD_reg[6:0], apbReg.pwdata[6:0], rwD_reg_update_0, 7'h00000000)

    bSizeRegSt roBsize_reg;
    assign roBsize_reg = roBsize.data;

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
        if (wr_select) begin
            case (apb_addr) inside
                32'h0 : begin
                    rwD_reg_update_0 = 1'b1;
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
        
        if (rd_select) begin
            case (apb_addr) inside
                32'h0 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(rwD_reg[6:0]);
                end
                32'h8 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(roBsize_reg[3:0]);
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
