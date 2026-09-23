//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkTableRegs
// GENERATED_CODE_BEGIN --template=moduleRegs
module twoClk_twoClkTableRegs
    // Generated Import package statement(s)
    import twoClk_package::*;
    #(
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst twoClkReg,
        memory_if.src tbl,
        input clk,
        input clkSlow,
        input rst_n,
        input rstSlow_n
    );

    twoClkRegAddrSt apb_addr;
    assign apb_addr = twoClkRegAddrSt'(twoClkReg.paddr) & 32'h3f;
    // Register/memory address offsets for decode documentation
    localparam int unsigned REG_TWOCLKTABLE_TBL = 32'h00000000; // Firmware-accessible table, reached from twoClkCpu through the twoClkTableRegs bridge
    localparam int unsigned REG_TWOCLKTABLE_TBL_SIZE = 32'h00000040; // Decode range size

    // tbl (bridged to clkSlow/rstSlow_n)
    twoClkTblSt nxt_tbl_data, tbl_data;   // write accumulation

    logic tbl_update_0;
    logic tbl_update_1;
    logic tbl_wr_sel, tbl_rd_sel, tbl_sel;
    logic nxt_tbl_req, tbl_req, tbl_acked;
    logic tbl_done, tbl_err;
    twoClkTblSt tbl_rdata;

    `DFFEN_DOM(clk, rst_n, tbl_data[31:0], nxt_tbl_data[31:0], tbl_update_0)
    `DFFEN_DOM(clk, rst_n, tbl_data[47:32], nxt_tbl_data[47:32], tbl_update_1)

    assign tbl_sel = tbl_wr_sel | tbl_rd_sel;
    assign nxt_tbl_req = tbl_sel & ~tbl_done & ~tbl_acked;
    `DFFR_DOM(clk, rst_n, tbl_req, nxt_tbl_req, '0)
    `DFFR_DOM(clk, rst_n, tbl_acked, (tbl_acked | tbl_done) & tbl_sel, '0)
    memory_reg_bridge #(.data_t(twoClkTblSt), .addr_t(twoClkTblAddrSt)) u_tbl_bridge (
        .bus_clk(clk), .bus_rst_n(rst_n), .mem_clk(clkSlow), .mem_rst_n(rstSlow_n),
        .req(tbl_req), .wr(tbl_wr_sel),
        .addr(twoClkTblAddrSt'(apb_addr[31:3])), .wdata(tbl_data),
        .done(tbl_done), .err(tbl_err), .rdata(tbl_rdata),
        .mem_port(tbl));

    logic wr_select;
    logic rd_select;
    assign wr_select = twoClkReg.psel & twoClkReg.penable & twoClkReg.pwrite & rst_n;
    assign rd_select = twoClkReg.psel & twoClkReg.penable & !twoClkReg.pwrite & rst_n;

    logic nxt_wr_ready, wr_ready;
    logic nxt_wr_slverr;
    always_comb begin
        nxt_wr_ready = 1'b0;
        nxt_wr_slverr = 1'b0;
        tbl_update_0 = 1'b0;
        tbl_update_1 = 1'b0;
        nxt_tbl_data = tbl_data;
        tbl_wr_sel = 1'b0;
        if (wr_select) begin
            case (apb_addr) inside
                [REG_TWOCLKTABLE_TBL:REG_TWOCLKTABLE_TBL + REG_TWOCLKTABLE_TBL_SIZE - 32'd4]: begin
                    case (apb_addr[2:0])
                        3'h0: begin
                            tbl_update_0 = 1'b1;
                            nxt_tbl_data[31:0] = twoClkReg.pwdata[31:0];
                        end
                        3'h4: begin
                            tbl_update_1 = 1'b1;
                            nxt_tbl_data[47:32] = twoClkReg.pwdata[15:0];
                            tbl_wr_sel = 1'b1;
                        end
                        default: ;
                    endcase
                end
                default: ; // unmapped/ro write: silently ignored (ACK below)
            endcase
            nxt_wr_ready = 1'b1;
            if (tbl_wr_sel) begin
                nxt_wr_ready = tbl_done;
                nxt_wr_slverr = tbl_done & tbl_err;
            end
        end
    end

    logic nxt_rd_ready, rd_ready;
    twoClkRegDataSt nxt_rd_data, rd_data;
    logic nxt_rd_slverr, nxt_slverr, slverr;
    always_comb begin
        nxt_rd_ready = 1'b0;
        nxt_rd_data = '0;
        nxt_rd_slverr = 1'b0;
        tbl_rd_sel = 1'b0;
        if (rd_select) begin
            case (apb_addr) inside
                [REG_TWOCLKTABLE_TBL:REG_TWOCLKTABLE_TBL + REG_TWOCLKTABLE_TBL_SIZE - 32'd4]: begin
                    case (apb_addr[2:0])
                        3'h0: begin
                            tbl_rd_sel = 1'b1;
                            if (tbl_done) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = twoClkRegDataSt'(tbl_rdata[31:0]);
                                nxt_rd_slverr = tbl_err;
                            end
                        end
                        3'h4: begin
                            tbl_rd_sel = 1'b1;
                            if (tbl_done) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = twoClkRegDataSt'(tbl_rdata[47:32]);
                                nxt_rd_slverr = tbl_err;
                            end
                        end
                        default: ;
                    endcase
                end
                default: begin // unmapped read: ACK with 0 (never stall, never error)
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = '0;
                end
            endcase
        end
    end
    assign nxt_slverr = nxt_wr_slverr | nxt_rd_slverr;

    // Update APB ready, read data and slave error. A same-domain access
    // never stalls. A bridged memory access holds pready low until its
    // bridge reports done, and returns pslverr when the memory's domain
    // was in reset during the access. Unmapped reads return 0.
    generate if (APB_READY_1WS)
        begin
            `DFFR_DOM(clk, rst_n, wr_ready,   nxt_wr_ready,   '0)
            `DFFR_DOM(clk, rst_n, rd_ready,   nxt_rd_ready,   '0)
            `DFFR_DOM(clk, rst_n, rd_data,    nxt_rd_data,    '0)
            `DFFR_DOM(clk, rst_n, slverr,     nxt_slverr,     '0)
        end else begin
            assign wr_ready   = nxt_wr_ready;
            assign rd_ready   = nxt_rd_ready;
            assign rd_data    = nxt_rd_data;
            assign slverr     = nxt_slverr;
        end
    endgenerate

    // Update the APB interface
    assign twoClkReg.prdata  = rd_data;
    assign twoClkReg.pready  = rd_ready | wr_ready;
    assign twoClkReg.pslverr = slverr;

endmodule : twoClk_twoClkTableRegs
// GENERATED_CODE_END
