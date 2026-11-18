//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=leafBRegs
// GENERATED_CODE_BEGIN --template=moduleRegs
module leafBRegs
    // Generated Import package statement(s)
    import ahbDecode_package::*;
    #(
        parameter bit AHB_READY_1WS = 0
    )
    (
        ahb_if.dst ahbReg,
        status_if.src cfgB,
        input clk,
        input rst_n
    );

    logic ahb_start;
    assign ahb_start = ahbReg.hsel & ahbReg.htrans[1] & ahbReg.hready;
    ahbAddrSt ahb_addr;
    `DFFEN_DOM(clk, rst_n, ahb_addr, ahbAddrSt'(ahbReg.haddr) & 32'h7, ahb_start)
    logic ahb_write, ahb_word;
    `DFFEN_DOM(clk, rst_n, ahb_write, ahbReg.hwrite, ahb_start)
    `DFFEN_DOM(clk, rst_n, ahb_word, ahbReg.hsize == 3'd2, ahb_start)
    logic ahb_dphase, ahb_ready, ahb_error, ahb_complete, ahb_err2, ahb_back2back;
    `DFF_DOM(clk, rst_n, ahb_dphase, ahb_start | (ahb_dphase & ~ahbReg.hreadyout))
    `DFF_DOM(clk, rst_n, ahb_err2, ahb_complete & ahb_error & ~ahb_err2)
    `DFF_DOM(clk, rst_n, ahb_back2back, ahb_start & ahb_dphase)
    logic [$bits(ahbReg.hrdata)-1:0] ahb_err_hrdata;
    `DFFEN_DOM(clk, rst_n, ahb_err_hrdata, ahbReg.hrdata, ahb_complete & ahb_error & ~ahb_err2)
    logic ahb_core_select, ahb_subword_wr, ahb_subword_err;
    assign ahb_core_select = ahb_dphase & ~ahb_err2 & ~ahb_back2back;
    assign ahb_subword_wr  = ahb_core_select & ahb_write & ~ahb_word;
    assign ahb_subword_err = ahb_subword_wr;
    // Register/memory address offsets for decode documentation
    localparam int unsigned REG_LEAFB_CFGB = 32'h00000000; // rw register

    cfgRegSt cfgB_reg;
    logic cfgB_reg_update_0;
    assign cfgB.data = cfgB_reg;
    `DFFREN_DOM(clk, rst_n, cfgB_reg[31:0], ahbReg.hwdata[31:0], cfgB_reg_update_0, 32'h00000000)

    logic wr_select;
    logic rd_select;
    assign wr_select = ahb_core_select & ahb_write & ahb_word & rst_n;
    assign rd_select = ahb_core_select & ~ahb_write & rst_n;

    logic nxt_wr_ready, wr_ready;
    logic nxt_wr_slverr, wr_slverr;
    always_comb begin
        nxt_wr_ready = 1'b0;
        nxt_wr_slverr = 1'b0;
        cfgB_reg_update_0 = 1'b0;
        if (wr_select) begin
            case (ahb_addr) inside
                REG_LEAFB_CFGB : begin
                    cfgB_reg_update_0 = 1'b1;
                end
                default: nxt_wr_slverr = 1'b1; // unmapped write: dropped, completes with HRESP ERROR
            endcase
            nxt_wr_ready = 1'b1;
        end
    end

    logic nxt_rd_ready, rd_ready;
    ahbDataSt nxt_rd_data, rd_data;
    logic nxt_rd_slverr, rd_slverr;
    always_comb begin
        nxt_rd_ready = 1'b0;
        nxt_rd_data = '0;
        nxt_rd_slverr = 1'b0;
        if (rd_select) begin
            case (ahb_addr) inside
                REG_LEAFB_CFGB : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = ahbDataSt'(cfgB_reg[31:0]);
                end
                default: begin // unmapped read: ACK with 32'hBADD_C0DE and HRESP ERROR
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = ahbDataSt'(32'hBADD_C0DE);
                    nxt_rd_slverr = 1'b1;
                end
            endcase
        end
    end

    // Update AHB ready, read data and error. Every access completes,
    // though the front end may add wait states. An unmapped access, or an ext
    // register write its owner refuses, returns HRESP ERROR; unmapped reads
    // also return 32'hBADD_C0DE.
    generate if (AHB_READY_1WS)
        begin
            `DFFR_DOM(clk, rst_n, wr_ready,   nxt_wr_ready,   '0)
            `DFFR_DOM(clk, rst_n, rd_ready,   nxt_rd_ready,   '0)
            `DFFR_DOM(clk, rst_n, rd_data,    nxt_rd_data,    '0)
            `DFFR_DOM(clk, rst_n, wr_slverr,  nxt_wr_slverr,  '0)
            `DFFR_DOM(clk, rst_n, rd_slverr,  nxt_rd_slverr,  '0)
        end else begin
            assign wr_ready   = nxt_wr_ready;
            assign rd_ready   = nxt_rd_ready;
            assign rd_data    = nxt_rd_data;
            assign wr_slverr  = nxt_wr_slverr;
            assign rd_slverr  = nxt_rd_slverr;
        end
    endgenerate

    // Update the AHB interface
    assign ahb_ready = rd_ready | wr_ready | ahb_subword_wr;
    assign ahb_error = wr_slverr | rd_slverr | ahb_subword_err;
    assign ahb_complete = ahb_dphase & ahb_ready;
    assign ahbReg.hrdata    = ahb_err2 ? ahb_err_hrdata : rd_data;
    assign ahbReg.hreadyout = ~ahb_dphase | (ahb_complete & ~ahb_error) | ahb_err2;
    assign ahbReg.hresp     = (ahb_complete & ahb_error) | ahb_err2;

endmodule : leafBRegs
// GENERATED_CODE_END
