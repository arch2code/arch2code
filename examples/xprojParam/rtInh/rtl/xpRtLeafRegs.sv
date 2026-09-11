//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtLeafRegs
// GENERATED_CODE_BEGIN --template=moduleRegs
module xpRtInh_xpRtLeafRegs
    // Generated Import package statement(s)
    import common_shared_types_package::*;
    import xpRtInh_package::*;
    #(
        parameter RT_WIDTH,
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst apbReg,
        status_if.src cfg,
        input clk,
        input rst_n
    );
    // Module-local parameterizable type/struct declarations (SV cannot
    // parameterize a package, so these live in the owning module).
    typedef logic[RT_WIDTH-1:0] cfgDataT; //xpRtLeaf configuration payload
    typedef struct packed {
        cfgDataT value; //xpRtLeaf configuration value
    } cfgSt;

    apbAddrSt apb_addr;
    assign apb_addr = apbAddrSt'(apbReg.paddr) & 32'h7;
    // Register/memory address offsets for decode documentation
    localparam int unsigned REG_XPRTLEAF_CFG = 32'h00000000; // xpRtLeaf configuration register

    genvar gi;

    cfgSt cfg_reg;
    localparam int unsigned CFG_W = $bits(cfgSt);
    logic [31:0] cfg_rword [0:0];
    logic [0:0] cfg_update;
    assign cfg.data = cfg_reg;
    localparam logic [31:0] cfg_rst [0:0] = '{ 32'h00000000 };
    generate
        for (gi = 0; gi < 1; gi++) begin : g_cfg
            if (CFG_W > 32*gi) begin : present
                if (CFG_W >= 32*(gi+1)) begin : full
                    `DFFREN(cfg_reg[32*gi +: 32], apbReg.pwdata[31:0], cfg_update[gi], cfg_rst[gi])
                    assign cfg_rword[gi] = cfg_reg[32*gi +: 32];
                end else begin : partial
                    `DFFREN(cfg_reg[32*gi +: (CFG_W-32*gi)], apbReg.pwdata[CFG_W-32*gi-1:0], cfg_update[gi], cfg_rst[gi][(CFG_W-32*gi-1):0])
                    assign cfg_rword[gi] = 32'(cfg_reg[32*gi +: (CFG_W-32*gi)]);
                end
            end else begin : absent
                assign cfg_rword[gi] = '0; // absent word reads 0
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
        cfg_update = '0;
        if (wr_select) begin
            case (apb_addr) inside
                REG_XPRTLEAF_CFG : begin
                    cfg_update[0] = 1'b1;
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
                REG_XPRTLEAF_CFG : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(cfg_rword[0]);
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
            `DFFR(wr_ready,   nxt_wr_ready,   '0)
            `DFFR(rd_ready,   nxt_rd_ready,   '0)
            `DFFR(rd_data,    nxt_rd_data,    '0)
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

endmodule : xpRtInh_xpRtLeafRegs
// GENERATED_CODE_END
