//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkTableRegs
// GENERATED_CODE_BEGIN --template=moduleRegs
module twoClkTableRegs
    // Generated Import package statement(s)
    import twoClk_package::*;
    #(
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst twoClkReg,
        memory_if.src tbl,
        memory_if.src lut,
        memory_if.src stats,
        input clk,
        input rst_n
    );

    twoClkRegAddrSt apb_addr;
    assign apb_addr = twoClkRegAddrSt'(twoClkReg.paddr) & 32'h7f;
    // Register/memory address offsets for decode documentation
    localparam int unsigned REG_TWOCLKTABLE_TBL = 32'h00000000; // Firmware-accessible table, written and read by twoClkCpu through port B on clk
    localparam int unsigned REG_TWOCLKTABLE_TBL_SIZE = 32'h00000040; // Decode range size
    localparam int unsigned REG_TWOCLKTABLE_LUT = 32'h00000040; // Loaded by twoClkCpu through port B on clk, read by the sweep through port A on clkSlow
    localparam int unsigned REG_TWOCLKTABLE_LUT_SIZE = 32'h00000010; // Decode range size
    localparam int unsigned REG_TWOCLKTABLE_STATS = 32'h00000050; // Written by the sweep through port B on clkSlow, read by twoClkCpu through port A on clk
    localparam int unsigned REG_TWOCLKTABLE_STATS_SIZE = 32'h00000010; // Decode range size

    // tbl
    twoClkTblSt nxt_tbl_data, tbl_data;
    twoClkTblAddrSt tbl_addr;

    logic tbl_update_0;
    logic tbl_update_1;
    logic nxt_tbl_rd_enable, tbl_rd_enable, tbl_rd_capture;
    logic tbl_wr_enable;

    `DFF_DOM(clk, rst_n, tbl_addr, twoClkTblAddrSt'(apb_addr[31:3]))
    `DFF_DOM(clk, rst_n, tbl_wr_enable, tbl_update_1)
    `DFF_DOM(clk, rst_n, tbl_rd_enable, nxt_tbl_rd_enable)
    `DFF_DOM(clk, rst_n, tbl_rd_capture, tbl_rd_enable)

    `DFFEN_DOM(clk, rst_n, tbl_data[31:0], nxt_tbl_data[31:0], tbl_update_0)
    `DFFEN_DOM(clk, rst_n, tbl_data[47:32], nxt_tbl_data[47:32], tbl_update_1)

    assign tbl.enable      = tbl_rd_enable | tbl_wr_enable;
    assign tbl.wr_en       = tbl_wr_enable;
    assign tbl.addr        = tbl_addr;
    assign tbl.write_data  = tbl_data;

    // lut
    twoClkLutSt nxt_lut_data, lut_data;
    twoClkLutAddrSt lut_addr;

    logic lut_update_0;
    logic lut_wr_enable;

    `DFF_DOM(clk, rst_n, lut_addr, twoClkLutAddrSt'(apb_addr[31:2]))
    `DFF_DOM(clk, rst_n, lut_wr_enable, lut_update_0)

    `DFFEN_DOM(clk, rst_n, lut_data[15:0], nxt_lut_data[15:0], lut_update_0)

    assign lut.enable      = lut_wr_enable;
    assign lut.wr_en       = lut_wr_enable;
    assign lut.addr        = lut_addr;
    assign lut.write_data  = lut_data;

    // stats
    twoClkLutAddrSt stats_addr;

    logic nxt_stats_rd_enable, stats_rd_enable, stats_rd_capture;

    `DFF_DOM(clk, rst_n, stats_addr, twoClkLutAddrSt'(apb_addr[31:2]))
    `DFF_DOM(clk, rst_n, stats_rd_enable, nxt_stats_rd_enable)
    `DFF_DOM(clk, rst_n, stats_rd_capture, stats_rd_enable)

    assign stats.enable      = stats_rd_enable;
    assign stats.wr_en       = 1'b0;
    assign stats.addr        = stats_addr;
    assign stats.write_data  = '0;

    logic wr_select;
    logic rd_select;
    assign wr_select = twoClkReg.psel & twoClkReg.penable & twoClkReg.pwrite & rst_n;
    assign rd_select = twoClkReg.psel & twoClkReg.penable & !twoClkReg.pwrite & rst_n;

    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_ready = 1'b0;
        tbl_update_0 = 1'b0;
        tbl_update_1 = 1'b0;
        nxt_tbl_data = tbl_data;
        lut_update_0 = 1'b0;
        nxt_lut_data = lut_data;
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
                        end
                        default: ;
                    endcase
                end
                [REG_TWOCLKTABLE_LUT:REG_TWOCLKTABLE_LUT + REG_TWOCLKTABLE_LUT_SIZE - 32'd4]: begin
                    case (apb_addr[1:0])
                        2'h0: begin
                            lut_update_0 = 1'b1;
                            nxt_lut_data[15:0] = twoClkReg.pwdata[15:0];
                        end
                        default: ;
                    endcase
                end
                [REG_TWOCLKTABLE_STATS:REG_TWOCLKTABLE_STATS + REG_TWOCLKTABLE_STATS_SIZE - 32'd4]: ; // read-only to firmware: the write is dropped
                default: ; // unmapped/ro write: silently ignored (ACK below)
            endcase
            nxt_wr_ready = 1'b1;
        end
    end

    logic nxt_rd_ready, rd_ready;
    twoClkRegDataSt nxt_rd_data, rd_data;
    always_comb begin
        nxt_rd_ready = 1'b0;
        nxt_rd_data = '0;
        nxt_tbl_rd_enable = 1'b0;
        nxt_stats_rd_enable = 1'b0;
        if (rd_select) begin
            case (apb_addr) inside
                [REG_TWOCLKTABLE_TBL:REG_TWOCLKTABLE_TBL + REG_TWOCLKTABLE_TBL_SIZE - 32'd4]: begin
                    case (apb_addr[2:0])
                        3'h0: begin
                            if (tbl_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = twoClkRegDataSt'(tbl.read_data[31:0]);
                            end
                        end
                        3'h4: begin
                            if (tbl_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = twoClkRegDataSt'(tbl.read_data[47:32]);
                            end
                        end
                        default: begin
                            nxt_rd_ready = 1'b1;
                            nxt_rd_data = '0;
                        end
                    endcase
                    nxt_tbl_rd_enable = (apb_addr[2:0] inside {3'h0, 3'h4}) & ~tbl_rd_capture;
                end
                [REG_TWOCLKTABLE_LUT:REG_TWOCLKTABLE_LUT + REG_TWOCLKTABLE_LUT_SIZE - 32'd4]: begin // write-only to firmware: reads return 0
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = '0;
                end
                [REG_TWOCLKTABLE_STATS:REG_TWOCLKTABLE_STATS + REG_TWOCLKTABLE_STATS_SIZE - 32'd4]: begin
                    case (apb_addr[1:0])
                        2'h0: begin
                            if (stats_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = twoClkRegDataSt'(stats.read_data[15:0]);
                            end
                        end
                        default: begin
                            nxt_rd_ready = 1'b1;
                            nxt_rd_data = '0;
                        end
                    endcase
                    nxt_stats_rd_enable = (apb_addr[1:0] inside {2'h0}) & ~stats_rd_capture;
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
    assign twoClkReg.prdata  = rd_data;
    assign twoClkReg.pready  = rd_ready | wr_ready;
    assign twoClkReg.pslverr = 1'b0;

endmodule : twoClkTableRegs
// GENERATED_CODE_END
