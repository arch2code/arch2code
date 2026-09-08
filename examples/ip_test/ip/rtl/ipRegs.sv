//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipRegs
// GENERATED_CODE_BEGIN --template=moduleRegs
module ip_ipRegs
    // Generated Import package statement(s)
    import ip_package::*;
    #(
        parameter IP_DATA_WIDTH,
        parameter IP_MEM_DEPTH,
        parameter IP_NONCONST_DEPTH,
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst ipReg,
        status_if.src ipCfg,
        status_if.dst ipLastData,
        memory_if.src ipMem,
        memory_if.src ipFixedMem,
        memory_if.src ipNonConstMem,
        input clk,
        input rst_n
    );
    // Module-local parameterizable type/struct declarations (SV cannot
    // parameterize a package, so these live in the owning module).
    localparam IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2; //Derived width, 2x data (maxValue auto-derived); eval-derived, lives in constants: since no block param consumes it
    localparam IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2; //Second-level derived width, 4x data
    localparam IP_MEM_DEPTH_X2 = IP_MEM_DEPTH * 2; //Derived memory depth, 2x depth
    localparam IP_MEM_DEPTH_X4 = IP_MEM_DEPTH_X2 * 2; //Second-level derived memory depth, 4x depth
    typedef logic[IP_DATA_WIDTH-1:0] ipDataT; //IP data word, parameterizable
    typedef logic[$clog2(IP_MEM_DEPTH)-1:0] ipMemAddrT; //Index into ipMem (0 .. IP_MEM_DEPTH-1)
    typedef logic[IP_DATA_WIDTH_X4-1:0] ipDerivedWidthT; //Type sized by a second-level eval-derived localparam
    typedef logic[$clog2(IP_MEM_DEPTH_X4)-1:0] ipDerivedMemAddrT; //Index into second-level derived-depth memory
    typedef logic signed[IP_MEM_DEPTH-1:0] ipSignedParamT; //Signed parameterizable value, width tracks IP_MEM_DEPTH
    typedef struct packed {
        enableT marker; //Marker bit expected after the data payload
        ipDataT data; //Data word
    } ipDataSt;
    typedef struct packed {
        enableT enable; //Enable bit
        ipModeT mode; //Operating mode
        ipDataT threshold; //Threshold value
    } ipCfgSt;
    typedef struct packed {
        ipDataT data; //Data word
    } ipMemSt;
    typedef struct packed {
        ipMemAddrT address; //Memory address
    } ipMemAddrSt;
    typedef struct packed {
        ipDataT [IP_MEM_DEPTH-1:0] samples; //Burst of parameterizable samples
    } ipBurstSt;
    typedef struct packed {
        ipDerivedMemAddrT address; //Second-level derived-depth memory address
    } ipDerivedMemAddrSt;
    typedef struct packed {
        ipCfgSt cfg; //Single nested parameterizable config sub-struct
        ipDataSt [2-1:0] payloads; //Parameterizable nested sub-struct array
    } ipParamNestedSt;
    typedef struct packed {
        ipSignedParamT offset; //Signed parameterizable field
        ipMemAddrT index; //Unsigned parameterizable field below it
    } ipSignedParamSt;

    ipRegAddrSt apb_addr;
    assign apb_addr = ipRegAddrSt'(ipReg.paddr) & 32'h3ff;
    // Register/memory address offsets for decode documentation
    localparam int unsigned REG_IP_IPMEM = 32'h00000000; // IP scratch memory (FW-accessible)
    localparam int unsigned REG_IP_IPMEM_SIZE = 32'h00000200; // Decode range size
    localparam int unsigned REG_IP_IPFIXEDMEM = 32'h00000200; // Fixed-struct memory with block-param wordLines (F2.4 regression)
    localparam int unsigned REG_IP_IPFIXEDMEM_SIZE = 32'h00000080; // Decode range size
    localparam int unsigned REG_IP_IPNONCONSTMEM = 32'h00000280; // Block-param wordLines with no backing constant (worst-case sizing regression)
    localparam int unsigned REG_IP_IPNONCONSTMEM_SIZE = 32'h00000060; // Decode range size
    localparam int unsigned REG_IP_IPCFG = 32'h00000300; // IP configuration
    localparam int unsigned REG_IP_IPLASTDATA = 32'h00000318; // Last data word received on ipDataIf

    genvar gi;

    ipCfgSt ipCfg_reg;
    localparam int unsigned IPCFG_W = $bits(ipCfgSt);
    logic [31:0] ipCfg_rword [0:2];
    logic [2:0] ipCfg_update;
    assign ipCfg.data = ipCfg_reg;
    localparam logic [31:0] ipCfg_rst [0:2] = '{ 32'h00000042, 32'h00000000, 32'h00000000 };
    generate
        for (gi = 0; gi < 3; gi++) begin : g_ipCfg
            if (IPCFG_W > 32*gi) begin : present
                if (IPCFG_W >= 32*(gi+1)) begin : full
                    `DFFREN_CLK(clk, ipCfg_reg[32*gi +: 32], ipReg.pwdata[31:0], ipCfg_update[gi], ipCfg_rst[gi])
                    assign ipCfg_rword[gi] = ipCfg_reg[32*gi +: 32];
                end else begin : partial
                    `DFFREN_CLK(clk, ipCfg_reg[32*gi +: (IPCFG_W-32*gi)], ipReg.pwdata[IPCFG_W-32*gi-1:0], ipCfg_update[gi], ipCfg_rst[gi][(IPCFG_W-32*gi-1):0])
                    assign ipCfg_rword[gi] = 32'(ipCfg_reg[32*gi +: (IPCFG_W-32*gi)]);
                end
            end else begin : absent
                assign ipCfg_rword[gi] = '0; // absent word reads 0
            end
        end
    endgenerate

    ipDataSt ipLastData_reg;
    localparam int unsigned IPLASTDATA_W = $bits(ipDataSt);
    logic [31:0] ipLastData_rword [0:2];
    assign ipLastData_reg = ipLastData.data;
    generate
        for (gi = 0; gi < 3; gi++) begin : g_ipLastData
            if (IPLASTDATA_W > 32*gi) begin : present
                if (IPLASTDATA_W >= 32*(gi+1)) begin : full
                    assign ipLastData_rword[gi] = ipLastData_reg[32*gi +: 32];
                end else begin : partial
                    assign ipLastData_rword[gi] = 32'(ipLastData_reg[32*gi +: (IPLASTDATA_W-32*gi)]);
                end
            end else begin : absent
                assign ipLastData_rword[gi] = '0; // absent word reads 0
            end
        end
    endgenerate

    // ipMem
    ipMemSt ipMem_reg;
    localparam int unsigned IPMEM_W = $bits(ipMemSt);
    localparam int unsigned IPMEM_TOP = (IPMEM_W-1)/32; // top present word for this variant
    logic [2:0] ipMem_update;
    logic [31:0] ipMem_rword [0:2];
    ipMemAddrSt ipMem_addr;
    logic nxt_ipMem_rd_enable, ipMem_rd_enable, ipMem_rd_capture;
    logic ipMem_wr_enable;
    `DFF_CLK(clk, ipMem_addr, ipMemAddrSt'(apb_addr[31:4]))
    `DFF_CLK(clk, ipMem_wr_enable, ipMem_update[IPMEM_TOP])
    `DFF_CLK(clk, ipMem_rd_enable, nxt_ipMem_rd_enable)
    `DFF_CLK(clk, ipMem_rd_capture, ipMem_rd_enable)
    generate
        for (gi = 0; gi < 3; gi++) begin : g_ipMem
            if (IPMEM_W > 32*gi) begin : present
                if (IPMEM_W >= 32*(gi+1)) begin : full
                    `DFFEN_CLK(clk, ipMem_reg[32*gi +: 32], ipReg.pwdata[31:0], ipMem_update[gi])
                    assign ipMem_rword[gi] = ipMem.read_data[32*gi +: 32];
                end else begin : partial
                    `DFFEN_CLK(clk, ipMem_reg[32*gi +: (IPMEM_W-32*gi)], ipReg.pwdata[IPMEM_W-32*gi-1:0], ipMem_update[gi])
                    assign ipMem_rword[gi] = 32'(ipMem.read_data[32*gi +: (IPMEM_W-32*gi)]);
                end
            end else begin : absent
                assign ipMem_rword[gi] = '0; // absent word reads 0
            end
        end
    endgenerate
    assign ipMem.enable      = ipMem_rd_enable | ipMem_wr_enable;
    assign ipMem.wr_en       = ipMem_wr_enable;
    assign ipMem.addr        = ipMem_addr;
    assign ipMem.write_data  = ipMem_reg;

    // ipFixedMem
    ipFixedSt nxt_ipFixedMem_data, ipFixedMem_data;
    ipFixedAddrSt ipFixedMem_addr;

    logic ipFixedMem_update_0;
    logic nxt_ipFixedMem_rd_enable, ipFixedMem_rd_enable, ipFixedMem_rd_capture;
    logic ipFixedMem_wr_enable;

    `DFF_CLK(clk, ipFixedMem_addr, ipFixedAddrSt'(apb_addr[31:2]))
    `DFF_CLK(clk, ipFixedMem_wr_enable, ipFixedMem_update_0)
    `DFF_CLK(clk, ipFixedMem_rd_enable, nxt_ipFixedMem_rd_enable)
    `DFF_CLK(clk, ipFixedMem_rd_capture, ipFixedMem_rd_enable)

    `DFFEN_CLK(clk, ipFixedMem_data[7:0], nxt_ipFixedMem_data[7:0], ipFixedMem_update_0)

    assign ipFixedMem.enable      = ipFixedMem_rd_enable | ipFixedMem_wr_enable;
    assign ipFixedMem.wr_en       = ipFixedMem_wr_enable;
    assign ipFixedMem.addr        = ipFixedMem_addr;
    assign ipFixedMem.write_data  = ipFixedMem_data;

    // ipNonConstMem
    ipFixedSt nxt_ipNonConstMem_data, ipNonConstMem_data;
    ipFixedAddrSt ipNonConstMem_addr;

    logic ipNonConstMem_update_0;
    logic nxt_ipNonConstMem_rd_enable, ipNonConstMem_rd_enable, ipNonConstMem_rd_capture;
    logic ipNonConstMem_wr_enable;

    `DFF_CLK(clk, ipNonConstMem_addr, ipFixedAddrSt'(apb_addr[31:2]))
    `DFF_CLK(clk, ipNonConstMem_wr_enable, ipNonConstMem_update_0)
    `DFF_CLK(clk, ipNonConstMem_rd_enable, nxt_ipNonConstMem_rd_enable)
    `DFF_CLK(clk, ipNonConstMem_rd_capture, ipNonConstMem_rd_enable)

    `DFFEN_CLK(clk, ipNonConstMem_data[7:0], nxt_ipNonConstMem_data[7:0], ipNonConstMem_update_0)

    assign ipNonConstMem.enable      = ipNonConstMem_rd_enable | ipNonConstMem_wr_enable;
    assign ipNonConstMem.wr_en       = ipNonConstMem_wr_enable;
    assign ipNonConstMem.addr        = ipNonConstMem_addr;
    assign ipNonConstMem.write_data  = ipNonConstMem_data;

    logic wr_select;
    logic rd_select;
    assign wr_select = ipReg.psel & ipReg.penable & ipReg.pwrite & rst_n;
    assign rd_select = ipReg.psel & ipReg.penable & !ipReg.pwrite & rst_n;

    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_ready = 1'b0;
        ipCfg_update = '0;
        ipMem_update = '0;
        ipFixedMem_update_0 = 1'b0;
        nxt_ipFixedMem_data = ipFixedMem_data;
        ipNonConstMem_update_0 = 1'b0;
        nxt_ipNonConstMem_data = ipNonConstMem_data;
        if (wr_select) begin
            case (apb_addr) inside
                REG_IP_IPCFG : begin
                    ipCfg_update[0] = 1'b1;
                end
                REG_IP_IPCFG + 32'd4 : begin
                    ipCfg_update[1] = 1'b1;
                end
                REG_IP_IPCFG + 32'd8 : begin
                    ipCfg_update[2] = 1'b1;
                end
                [REG_IP_IPMEM:REG_IP_IPMEM + REG_IP_IPMEM_SIZE - 32'd4]: begin
                    case (apb_addr[3:0])
                        4'h0: ipMem_update[0] = 1'b1;
                        4'h4: ipMem_update[1] = 1'b1;
                        4'h8: ipMem_update[2] = 1'b1;
                        default: ;
                    endcase
                end
                [REG_IP_IPFIXEDMEM:REG_IP_IPFIXEDMEM + REG_IP_IPFIXEDMEM_SIZE - 32'd4]: begin
                    case (apb_addr[1:0])
                        2'h0: begin
                            ipFixedMem_update_0 = 1'b1;
                            nxt_ipFixedMem_data[7:0] = ipReg.pwdata[7:0];
                        end
                        default: ;
                    endcase
                end
                [REG_IP_IPNONCONSTMEM:REG_IP_IPNONCONSTMEM + REG_IP_IPNONCONSTMEM_SIZE - 32'd4]: begin
                    case (apb_addr[1:0])
                        2'h0: begin
                            ipNonConstMem_update_0 = 1'b1;
                            nxt_ipNonConstMem_data[7:0] = ipReg.pwdata[7:0];
                        end
                        default: ;
                    endcase
                end
                default: ; // unmapped/ro write: silently ignored (ACK below)
            endcase
            nxt_wr_ready = 1'b1;
        end
    end

    logic nxt_rd_ready, rd_ready;
    ipRegDataSt nxt_rd_data, rd_data;
    always_comb begin
        nxt_rd_ready = 1'b0;
        nxt_rd_data = '0;
        nxt_ipMem_rd_enable = 1'b0;
        nxt_ipFixedMem_rd_enable = 1'b0;
        nxt_ipNonConstMem_rd_enable = 1'b0;
        if (rd_select) begin
            case (apb_addr) inside
                REG_IP_IPCFG : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = ipRegDataSt'(ipCfg_rword[0]);
                end
                REG_IP_IPCFG + 32'd4 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = ipRegDataSt'(ipCfg_rword[1]);
                end
                REG_IP_IPCFG + 32'd8 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = ipRegDataSt'(ipCfg_rword[2]);
                end
                REG_IP_IPLASTDATA : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = ipRegDataSt'(ipLastData_rword[0]);
                end
                REG_IP_IPLASTDATA + 32'd4 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = ipRegDataSt'(ipLastData_rword[1]);
                end
                REG_IP_IPLASTDATA + 32'd8 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = ipRegDataSt'(ipLastData_rword[2]);
                end
                [REG_IP_IPMEM:REG_IP_IPMEM + REG_IP_IPMEM_SIZE - 32'd4]: begin
                    case (apb_addr[3:0])
                        4'h0: begin
                            if (ipMem_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = ipRegDataSt'(ipMem_rword[0]);
                            end
                        end
                        4'h4: begin
                            if (ipMem_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = ipRegDataSt'(ipMem_rword[1]);
                            end
                        end
                        4'h8: begin
                            if (ipMem_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = ipRegDataSt'(ipMem_rword[2]);
                            end
                        end
                        default: begin
                            nxt_rd_ready = 1'b1;
                            nxt_rd_data = '0;
                        end
                    endcase
                    nxt_ipMem_rd_enable = (apb_addr[3:0] inside {4'h0, 4'h4, 4'h8}) & ~ipMem_rd_capture;
                end
                [REG_IP_IPFIXEDMEM:REG_IP_IPFIXEDMEM + REG_IP_IPFIXEDMEM_SIZE - 32'd4]: begin
                    case (apb_addr[1:0])
                        2'h0: begin
                            if (ipFixedMem_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = ipRegDataSt'(ipFixedMem.read_data[7:0]);
                            end
                        end
                        default: ;
                    endcase
                    nxt_ipFixedMem_rd_enable = ~ipFixedMem_rd_capture;
                end
                [REG_IP_IPNONCONSTMEM:REG_IP_IPNONCONSTMEM + REG_IP_IPNONCONSTMEM_SIZE - 32'd4]: begin
                    case (apb_addr[1:0])
                        2'h0: begin
                            if (ipNonConstMem_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = ipRegDataSt'(ipNonConstMem.read_data[7:0]);
                            end
                        end
                        default: ;
                    endcase
                    nxt_ipNonConstMem_rd_enable = ~ipNonConstMem_rd_capture;
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
    assign ipReg.prdata  = rd_data;
    assign ipReg.pready  = rd_ready | wr_ready;
    assign ipReg.pslverr = 1'b0;

endmodule : ip_ipRegs
// GENERATED_CODE_END
