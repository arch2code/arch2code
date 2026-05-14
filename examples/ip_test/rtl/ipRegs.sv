//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipRegs
// GENERATED_CODE_BEGIN --template=moduleRegs
module ipRegs
    // Generated Import package statement(s)
    import ip_top_package::*;
    import ip_package::*;
    #(
        parameter bit APB_READY_1WS = 0
    )
    (
        apb_if.dst apbReg,
        status_if.src ipCfg,
        status_if.dst ipLastData,
        memory_if.src ipMem,
        memory_if.src ipFixedMem,
        memory_if.src ipNonConstMem,
        input clk,
        input rst_n
    );

    apbAddrSt apb_addr;
    assign apb_addr = apbAddrSt'(apbReg.paddr) & 32'h3ff;
    // Register/memory address offsets for decode documentation
    localparam int unsigned REG_IP_IPMEM = 32'h00000000; // IP scratch memory (FW-accessible)
    localparam int unsigned REG_IP_IPMEM_SIZE = 32'h00000100; // Decode range size
    localparam int unsigned REG_IP_IPFIXEDMEM = 32'h00000200; // Fixed-struct memory with block-param wordLines (F2.4 regression)
    localparam int unsigned REG_IP_IPFIXEDMEM_SIZE = 32'h00000040; // Decode range size
    localparam int unsigned REG_IP_IPNONCONSTMEM = 32'h00000280; // Block-param wordLines with no backing constant (worst-case sizing regression)
    localparam int unsigned REG_IP_IPNONCONSTMEM_SIZE = 32'h00000060; // Decode range size
    localparam int unsigned REG_IP_IPCFG = 32'h00000300; // IP configuration
    localparam int unsigned REG_IP_IPLASTDATA = 32'h00000318; // Last data word received on ipDataIf

    ipCfgSt ipCfg_reg;
    logic ipCfg_reg_update_0;
    logic ipCfg_reg_update_1;
    logic ipCfg_reg_update_2;
    assign ipCfg.data = ipCfg_reg;
    `DFFREN(ipCfg_reg[31:0], apbReg.pwdata[31:0], ipCfg_reg_update_0, 32'h00000000)
    `DFFREN(ipCfg_reg[63:32], apbReg.pwdata[31:0], ipCfg_reg_update_1, 32'h00000000)
    `DFFREN(ipCfg_reg[72:64], apbReg.pwdata[8:0], ipCfg_reg_update_2, 9'h00000000)

    ipDataSt ipLastData_reg;
    assign ipLastData_reg = ipLastData.data;

    // ipMem
    ipMemSt nxt_ipMem_data, ipMem_data;
    ipMemAddrSt ipMem_addr;

    logic ipMem_update_0;
    logic ipMem_update_1;
    logic ipMem_update_2;
    logic nxt_ipMem_rd_enable, ipMem_rd_enable, ipMem_rd_capture;
    logic ipMem_wr_enable;

    `DFF(ipMem_addr, ipMemAddrSt'(apb_addr[31:4]))
    `DFF(ipMem_wr_enable, ipMem_update_2)
    `DFF(ipMem_rd_enable, nxt_ipMem_rd_enable)
    `DFF(ipMem_rd_capture, ipMem_rd_enable)

    `DFFEN(ipMem_data[31:0], nxt_ipMem_data[31:0], ipMem_update_0)
    `DFFEN(ipMem_data[63:32], nxt_ipMem_data[63:32], ipMem_update_1)
    `DFFEN(ipMem_data[69:64], nxt_ipMem_data[69:64], ipMem_update_2)

    assign ipMem.enable      = ipMem_rd_enable | ipMem_wr_enable;
    assign ipMem.wr_en       = ipMem_wr_enable;
    assign ipMem.addr        = ipMem_addr;
    assign ipMem.write_data  = ipMem_data;

    // ipFixedMem
    ipFixedSt nxt_ipFixedMem_data, ipFixedMem_data;
    ipFixedAddrSt ipFixedMem_addr;

    logic ipFixedMem_update_0;
    logic nxt_ipFixedMem_rd_enable, ipFixedMem_rd_enable, ipFixedMem_rd_capture;
    logic ipFixedMem_wr_enable;

    `DFF(ipFixedMem_addr, ipFixedAddrSt'(apb_addr[31:2]))
    `DFF(ipFixedMem_wr_enable, ipFixedMem_update_0)
    `DFF(ipFixedMem_rd_enable, nxt_ipFixedMem_rd_enable)
    `DFF(ipFixedMem_rd_capture, ipFixedMem_rd_enable)

    `DFFEN(ipFixedMem_data[7:0], nxt_ipFixedMem_data[7:0], ipFixedMem_update_0)

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

    `DFF(ipNonConstMem_addr, ipFixedAddrSt'(apb_addr[31:2]))
    `DFF(ipNonConstMem_wr_enable, ipNonConstMem_update_0)
    `DFF(ipNonConstMem_rd_enable, nxt_ipNonConstMem_rd_enable)
    `DFF(ipNonConstMem_rd_capture, ipNonConstMem_rd_enable)

    `DFFEN(ipNonConstMem_data[7:0], nxt_ipNonConstMem_data[7:0], ipNonConstMem_update_0)

    assign ipNonConstMem.enable      = ipNonConstMem_rd_enable | ipNonConstMem_wr_enable;
    assign ipNonConstMem.wr_en       = ipNonConstMem_wr_enable;
    assign ipNonConstMem.addr        = ipNonConstMem_addr;
    assign ipNonConstMem.write_data  = ipNonConstMem_data;

    logic wr_select;
    logic rd_select;
    assign wr_select = apbReg.psel & apbReg.penable & apbReg.pwrite & rst_n;
    assign rd_select = apbReg.psel & apbReg.penable & !apbReg.pwrite & rst_n;

    logic nxt_wr_pslverr, wr_pslverr;
    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_pslverr = 1'b0;
        nxt_wr_ready = 1'b0;
        ipCfg_reg_update_0 = 1'b0;
        ipCfg_reg_update_1 = 1'b0;
        ipCfg_reg_update_2 = 1'b0;
        ipMem_update_0 = 1'b0;
        ipMem_update_1 = 1'b0;
        ipMem_update_2 = 1'b0;
        nxt_ipMem_data = ipMem_data;
        ipFixedMem_update_0 = 1'b0;
        nxt_ipFixedMem_data = ipFixedMem_data;
        ipNonConstMem_update_0 = 1'b0;
        nxt_ipNonConstMem_data = ipNonConstMem_data;
        if (wr_select) begin
            case (apb_addr) inside
                REG_IP_IPCFG : begin
                    ipCfg_reg_update_0 = 1'b1;
                end
                REG_IP_IPCFG + 32'd4 : begin
                    ipCfg_reg_update_1 = 1'b1;
                end
                REG_IP_IPCFG + 32'd8 : begin
                    ipCfg_reg_update_2 = 1'b1;
                end
                [REG_IP_IPMEM:REG_IP_IPMEM + REG_IP_IPMEM_SIZE - 32'd4]: begin
                    case (apb_addr[3:0])
                        4'h0: begin
                            ipMem_update_0 = 1'b1;
                            nxt_ipMem_data[31:0] = apbReg.pwdata[31:0];
                        end
                        4'h4: begin
                            ipMem_update_1 = 1'b1;
                            nxt_ipMem_data[63:32] = apbReg.pwdata[31:0];
                        end
                        4'h8: begin
                            ipMem_update_2 = 1'b1;
                            nxt_ipMem_data[69:64] = apbReg.pwdata[5:0];
                        end
                        default: ;
                    endcase
                end
                [REG_IP_IPFIXEDMEM:REG_IP_IPFIXEDMEM + REG_IP_IPFIXEDMEM_SIZE - 32'd4]: begin
                    case (apb_addr[1:0])
                        2'h0: begin
                            ipFixedMem_update_0 = 1'b1;
                            nxt_ipFixedMem_data[7:0] = apbReg.pwdata[7:0];
                        end
                        default: ;
                    endcase
                end
                [REG_IP_IPNONCONSTMEM:REG_IP_IPNONCONSTMEM + REG_IP_IPNONCONSTMEM_SIZE - 32'd4]: begin
                    case (apb_addr[1:0])
                        2'h0: begin
                            ipNonConstMem_update_0 = 1'b1;
                            nxt_ipNonConstMem_data[7:0] = apbReg.pwdata[7:0];
                        end
                        default: ;
                    endcase
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
        nxt_ipMem_rd_enable = 1'b0;
        nxt_ipFixedMem_rd_enable = 1'b0;
        nxt_ipNonConstMem_rd_enable = 1'b0;
        if (rd_select) begin
            case (apb_addr) inside
                REG_IP_IPCFG : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(ipCfg_reg[31:0]);
                end
                REG_IP_IPCFG + 32'd4 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(ipCfg_reg[63:32]);
                end
                REG_IP_IPCFG + 32'd8 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(ipCfg_reg[72:64]);
                end
                REG_IP_IPLASTDATA : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(ipLastData_reg[31:0]);
                end
                REG_IP_IPLASTDATA + 32'd4 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(ipLastData_reg[63:32]);
                end
                REG_IP_IPLASTDATA + 32'd8 : begin
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = apbDataSt'(ipLastData_reg[70:64]);
                end
                [REG_IP_IPMEM:REG_IP_IPMEM + REG_IP_IPMEM_SIZE - 32'd4]: begin
                    case (apb_addr[3:0])
                        4'h0: begin
                            if (ipMem_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(ipMem.read_data[31:0]);
                            end
                        end
                        4'h4: begin
                            if (ipMem_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(ipMem.read_data[63:32]);
                            end
                        end
                        4'h8: begin
                            if (ipMem_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(ipMem.read_data[69:64]);
                            end
                        end
                        default: ;
                    endcase
                    nxt_ipMem_rd_enable = ~ipMem_rd_capture;
                end
                [REG_IP_IPFIXEDMEM:REG_IP_IPFIXEDMEM + REG_IP_IPFIXEDMEM_SIZE - 32'd4]: begin
                    case (apb_addr[1:0])
                        2'h0: begin
                            if (ipFixedMem_rd_capture) begin
                                nxt_rd_ready = 1'b1;
                                nxt_rd_data = apbDataSt'(ipFixedMem.read_data[7:0]);
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
                                nxt_rd_data = apbDataSt'(ipNonConstMem.read_data[7:0]);
                            end
                        end
                        default: ;
                    endcase
                    nxt_ipNonConstMem_rd_enable = ~ipNonConstMem_rd_capture;
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

endmodule : ipRegs
// GENERATED_CODE_END
