//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockGRegs
// GENERATED_CODE_BEGIN --template=moduleRegs
module mixed_blockGRegs
    // Generated Import package statement(s)
    import mixed_package::*;
    #(
        parameter fred,
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst apbReg,
        status_if.src rwG,
        input clk,
        input rst_n
    );

    apbAddrSt apb_addr;
    assign apb_addr = apbAddrSt'(apbReg.paddr) & 32'h7;
    // Register/memory address offsets for decode documentation
    localparam int unsigned REG_BLOCKG_RWG = 32'h00000000; // A Read Write register owned by parameterized container blockG and forwarded to a leaf

    dRegSt rwG_reg;
    logic rwG_reg_update_0;
    assign rwG.data = rwG_reg;
    `DFFREN_CLK(clk, rwG_reg[6:0], apbReg.pwdata[6:0], rwG_reg_update_0, 7'h00000000)

    logic wr_select;
    logic rd_select;
    assign wr_select = apbReg.psel & apbReg.penable & apbReg.pwrite & rst_n;
    assign rd_select = apbReg.psel & apbReg.penable & !apbReg.pwrite & rst_n;

    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_ready = 1'b0;
        rwG_reg_update_0 = 1'b0;
        if (wr_select) begin
            case (apb_addr) inside
                REG_BLOCKG_RWG : begin
                    rwG_reg_update_0 = 1'b1;
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
        
        if (rd_select) begin
            case (apb_addr) inside
                REG_BLOCKG_RWG : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(rwG_reg[6:0]);
                end
                default: begin // unmapped read: ACK with 0 (never stall, never error)
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = '0;
                end
            endcase
        end
    end

    // Update APB ready and read data. The bus is never stalled and slave
    // error is never asserted: every access ACKs, unmapped reads return 0.
    generate if (APB_READY_1WS)
        begin
            `DFFR_CLK(clk, wr_ready,   nxt_wr_ready,   '0)
            `DFFR_CLK(clk, rd_ready,   nxt_rd_ready,   '0)
            `DFFR_CLK(clk, rd_data,    nxt_rd_data,    '0)
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

endmodule : mixed_blockGRegs
// GENERATED_CODE_END
