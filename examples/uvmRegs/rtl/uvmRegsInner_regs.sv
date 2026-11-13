//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsInner_regs
// GENERATED_CODE_BEGIN --template=moduleRegs
module uvmRegsInner_regs
    // Generated Import package statement(s)
    import uvmRegs_package::*;
    #(
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst apbReg,
        status_if.src tag,
        input clk,
        input rst_n
    );

    uvmRegsAddrSt apb_addr;
    assign apb_addr = uvmRegsAddrSt'(apbReg.paddr) & 32'h7;
    // Register/memory address offsets for decode documentation
    localparam int unsigned REG_UVMREGSINNER_TAG = 32'h00000000; // Byte off the datapath

    uvmRegsByteSt tag_reg;
    logic tag_reg_update_0;
    assign tag.data = tag_reg;
    `DFFREN_DOM(clk, rst_n, tag_reg[7:0], apbReg.pwdata[7:0], tag_reg_update_0, 8'h00000011)

    logic wr_select;
    logic rd_select;
    assign wr_select = apbReg.psel & apbReg.penable & apbReg.pwrite & rst_n;
    assign rd_select = apbReg.psel & apbReg.penable & !apbReg.pwrite & rst_n;

    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_ready = 1'b0;
        tag_reg_update_0 = 1'b0;
        if (wr_select) begin
            case (apb_addr) inside
                REG_UVMREGSINNER_TAG : begin
                    tag_reg_update_0 = 1'b1;
                end
                default: ; // unmapped/ro write: silently ignored (ACK below)
            endcase
            nxt_wr_ready = 1'b1;
        end
    end

    logic nxt_rd_ready, rd_ready;
    uvmRegsDataSt nxt_rd_data, rd_data;
    always_comb begin
        nxt_rd_ready = 1'b0;
        nxt_rd_data = '0;
        if (rd_select) begin
            case (apb_addr) inside
                REG_UVMREGSINNER_TAG : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = uvmRegsDataSt'(tag_reg[7:0]);
                end
                default: begin // unmapped read: ACK with 32'hBADD_C0DE (never stall, never error)
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = uvmRegsDataSt'(32'hBADD_C0DE);
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

endmodule : uvmRegsInner_regs
// GENERATED_CODE_END
