//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsStat_regs
// GENERATED_CODE_BEGIN --template=moduleRegs
module uvmRegsStat_regs
    // Generated Import package statement(s)
    import uvmRegs_package::*;
    #(
        parameter int unsigned UVM_REGS_TAB_W = 32'h0000_000C,
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst apbReg,
        status_if.src mode,
        status_if.dst count,
        external_reg_if.src scratch,
        memory_if.src tab,
        memory_if.src hist,
        input clk,
        input rst_n
    );
    // Module-local parameterizable type/struct declarations (SV cannot
    // parameterize a package, so these live in the owning module).
    typedef logic[UVM_REGS_TAB_W-1:0] uvmRegsTabT; //Tab row
    typedef struct packed {
        uvmRegsTabT entry; //XORed into each word whose low bits select the row
    } uvmRegsTabSt;

    uvmRegsAddrSt apb_addr;
    assign apb_addr = uvmRegsAddrSt'(apbReg.paddr) & 32'hff;
    // Register/memory address offsets for decode documentation
    localparam int unsigned REG_UVMREGSSTAT_HIST = 32'h00000000; // Last word of each low-bits value
    localparam int unsigned REG_UVMREGSSTAT_HIST_SIZE = 32'h00000020; // Decode range size
    localparam int unsigned REG_UVMREGSSTAT_TAB = 32'h00000040; // XOR table the block serves
    localparam int unsigned REG_UVMREGSSTAT_TAB_SIZE = UVM_REGS_TAB_ROWS * 32'd8; // Decode range size
    localparam int unsigned REG_UVMREGSSTAT_MODE = 32'h00000080; // Datapath mode
    localparam int unsigned REG_UVMREGSSTAT_COUNT = 32'h00000088; // Words passed
    localparam int unsigned REG_UVMREGSSTAT_SCRATCH = 32'h00000090; // Scratch value the block stores

    genvar gi;

    uvmRegsModeSt mode_reg;
    logic mode_reg_update_0;
    assign mode.data = mode_reg;
    `DFFREN_DOM(clk, rst_n, mode_reg[0:0], apbReg.pwdata[0:0], mode_reg_update_0, 1'h00000000)

    uvmRegsCountSt count_reg;
    assign count_reg = count.data;

    uvmRegsScratchSt scratch_reg;
    assign scratch_reg = scratch.rdata;

    // hist
    uvmRegsIdxSt hist_addr;

    logic nxt_hist_rd_enable, hist_rd_enable, hist_rd_capture;

    `DFF_DOM(clk, rst_n, hist_addr, uvmRegsIdxSt'((apb_addr - REG_UVMREGSSTAT_HIST) >> 2))
    `DFF_DOM(clk, rst_n, hist_rd_enable, nxt_hist_rd_enable)
    `DFF_DOM(clk, rst_n, hist_rd_capture, hist_rd_enable)

    assign hist.enable      = hist_rd_enable;
    assign hist.wr_en       = 1'b0;
    assign hist.addr        = hist_addr;
    assign hist.write_data  = '0;

    // tab
    uvmRegsTabSt tab_reg;
    localparam int unsigned TAB_W = $bits(uvmRegsTabSt);
    localparam int unsigned TAB_TOP = (TAB_W-1)/32; // top present word for this variant
    logic [1:0] tab_update;
    logic [31:0] tab_rword [0:1];
    uvmRegsIdxSt tab_addr;
    logic nxt_tab_rd_enable, tab_rd_enable, tab_rd_capture;
    logic tab_wr_enable;
    `DFF_DOM(clk, rst_n, tab_addr, uvmRegsIdxSt'((apb_addr - REG_UVMREGSSTAT_TAB) >> 3))
    `DFF_DOM(clk, rst_n, tab_wr_enable, tab_update[TAB_TOP])
    `DFF_DOM(clk, rst_n, tab_rd_enable, nxt_tab_rd_enable)
    `DFF_DOM(clk, rst_n, tab_rd_capture, tab_rd_enable)
    generate
        for (gi = 0; gi < 2; gi++) begin : g_tab
            if (TAB_W > 32*gi) begin : present
                if (TAB_W >= 32*(gi+1)) begin : full
                    `DFFEN_DOM(clk, rst_n, tab_reg[32*gi +: 32], apbReg.pwdata[31:0], tab_update[gi])
                    assign tab_rword[gi] = tab.read_data[32*gi +: 32];
                end else begin : partial
                    `DFFEN_DOM(clk, rst_n, tab_reg[32*gi +: (TAB_W-32*gi)], apbReg.pwdata[TAB_W-32*gi-1:0], tab_update[gi])
                    assign tab_rword[gi] = 32'(tab.read_data[32*gi +: (TAB_W-32*gi)]);
                end
            end else begin : absent
                assign tab_rword[gi] = '0; // absent word reads 0
            end
        end
    endgenerate
    assign tab.enable      = tab_rd_enable | tab_wr_enable;
    assign tab.wr_en       = tab_wr_enable;
    assign tab.addr        = tab_addr;
    assign tab.write_data  = tab_reg;

    logic wr_select;
    logic rd_select;
    assign wr_select = apbReg.psel & apbReg.penable & apbReg.pwrite & rst_n;
    assign rd_select = apbReg.psel & apbReg.penable & !apbReg.pwrite & rst_n;

    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_ready = 1'b0;
        mode_reg_update_0 = 1'b0;
        scratch.write = '0;
        scratch.wdata = '0;
        tab_update = '0;
        if (wr_select) begin
            case (apb_addr) inside
                REG_UVMREGSSTAT_MODE : begin
                    mode_reg_update_0 = 1'b1;
                end
                REG_UVMREGSSTAT_SCRATCH : begin
                    scratch.write = 1;
                    scratch.wdata[15:0] = apbReg.pwdata[15:0];
                end
                [REG_UVMREGSSTAT_HIST:REG_UVMREGSSTAT_HIST + REG_UVMREGSSTAT_HIST_SIZE - 32'd4]: ; // read-only to firmware: the write is dropped
                [REG_UVMREGSSTAT_TAB:REG_UVMREGSSTAT_TAB + REG_UVMREGSSTAT_TAB_SIZE - 32'd4]: begin
                    case (3'(apb_addr - REG_UVMREGSSTAT_TAB))
                        3'h0: tab_update[0] = 1'b1;
                        3'h4: tab_update[1] = 1'b1;
                        default: ;
                    endcase
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
        nxt_hist_rd_enable = 1'b0;
        nxt_tab_rd_enable = 1'b0;
        if (rd_select) begin
            case (apb_addr) inside
                REG_UVMREGSSTAT_MODE : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = uvmRegsDataSt'(mode_reg[0:0]);
                end
                REG_UVMREGSSTAT_COUNT : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = uvmRegsDataSt'(count_reg[15:0]);
                end
                REG_UVMREGSSTAT_SCRATCH : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = uvmRegsDataSt'(scratch_reg[15:0]);
                end
                [REG_UVMREGSSTAT_HIST:REG_UVMREGSSTAT_HIST + REG_UVMREGSSTAT_HIST_SIZE - 32'd4]: begin
                    case (2'(apb_addr - REG_UVMREGSSTAT_HIST))
                        2'h0: begin
                            if (hist_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = uvmRegsDataSt'(hist.read_data[15:0]);
                            end
                        end
                        default: begin
                            nxt_rd_ready = 1'b1;
                            nxt_rd_data = '0;
                        end
                    endcase
                    nxt_hist_rd_enable = (2'(apb_addr - REG_UVMREGSSTAT_HIST) inside {2'h0}) & ~hist_rd_capture;
                end
                [REG_UVMREGSSTAT_TAB:REG_UVMREGSSTAT_TAB + REG_UVMREGSSTAT_TAB_SIZE - 32'd4]: begin
                    case (3'(apb_addr - REG_UVMREGSSTAT_TAB))
                        3'h0: begin
                            if (tab_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = uvmRegsDataSt'(tab_rword[0]);
                            end
                        end
                        3'h4: begin
                            if (tab_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = uvmRegsDataSt'(tab_rword[1]);
                            end
                        end
                        default: begin
                            nxt_rd_ready = 1'b1;
                            nxt_rd_data = '0;
                        end
                    endcase
                    nxt_tab_rd_enable = (3'(apb_addr - REG_UVMREGSSTAT_TAB) inside {3'h0, 3'h4}) & ~tab_rd_capture;
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

endmodule : uvmRegsStat_regs
// GENERATED_CODE_END
