//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsScale_regs
// GENERATED_CODE_BEGIN --template=moduleRegs
module uvmRegsScale_regs
    // Generated Import package statement(s)
    import uvmRegs_package::*;
    #(
        parameter int unsigned UVM_REGS_SCALE_W = 32'h0000_0004,
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst apbReg,
        status_if.src offset,
        input clk,
        input rst_n
    );
    // Module-local parameterizable type/struct declarations (SV cannot
    // parameterize a package, so these live in the owning module).
    typedef logic[UVM_REGS_SCALE_W-1:0] uvmRegsScaleT; //Scale offset
    typedef struct packed {
        uvmRegsScaleT offset; //Added to each word
    } uvmRegsScaleSt;

    uvmRegsAddrSt apb_addr;
    assign apb_addr = uvmRegsAddrSt'(apbReg.paddr) & 32'h7;
    // Register/memory address offsets for decode documentation
    localparam int unsigned REG_UVMREGSSCALE_OFFSET = 32'h00000000; // Added to each word

    genvar gi;

    uvmRegsScaleSt offset_reg;
    localparam int unsigned OFFSET_W = $bits(uvmRegsScaleSt);
    logic [31:0] offset_rword [0:0];
    logic [0:0] offset_update;
    assign offset.data = offset_reg;
    localparam logic [31:0] offset_rst [0:0] = '{ 32'h00000001 };
    generate
        for (gi = 0; gi < 1; gi++) begin : g_offset
            if (OFFSET_W > 32*gi) begin : present
                if (OFFSET_W >= 32*(gi+1)) begin : full
                    `DFFREN_DOM(clk, rst_n, offset_reg[32*gi +: 32], apbReg.pwdata[31:0], offset_update[gi], offset_rst[gi])
                    assign offset_rword[gi] = offset_reg[32*gi +: 32];
                end else begin : partial
                    `DFFREN_DOM(clk, rst_n, offset_reg[32*gi +: (OFFSET_W-32*gi)], apbReg.pwdata[OFFSET_W-32*gi-1:0], offset_update[gi], offset_rst[gi][(OFFSET_W-32*gi-1):0])
                    assign offset_rword[gi] = 32'(offset_reg[32*gi +: (OFFSET_W-32*gi)]);
                end
            end else begin : absent
                assign offset_rword[gi] = '0; // absent word reads 0
            end
        end
    endgenerate

    logic wr_select;
    logic rd_select;
    assign wr_select = apbReg.psel & apbReg.penable & apbReg.pwrite & rst_n;
    assign rd_select = apbReg.psel & apbReg.penable & !apbReg.pwrite & rst_n;

    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_ready = 1'b0;
        offset_update = '0;
        if (wr_select) begin
            case (apb_addr) inside
                REG_UVMREGSSCALE_OFFSET : begin
                    offset_update[0] = 1'b1;
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
                REG_UVMREGSSCALE_OFFSET : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = uvmRegsDataSt'(offset_rword[0]);
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

endmodule : uvmRegsScale_regs
// GENERATED_CODE_END
