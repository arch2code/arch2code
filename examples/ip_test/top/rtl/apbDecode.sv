//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: ip_test_apbDecode
module ip_test_apbDecode
// Generated Import package statement(s)
import common_shared_types_package::*;
(
    apb_if.src apbReg_uBridge,
    apb_if.src apbReg_uIp0,
    apb_if.src apbReg_uIp1,
    apb_if.dst cpu_main,
    input clk, rst_n
);

apbAddrSt apb_addr;
assign apb_addr = apbAddrSt'(cpu_main.paddr) & apbAddrSt'(32'hfff_ffff);
//signals for interface cpu_main
apbAddrSt paddr_q;
`DFF_CLK(clk, paddr_q, cpu_main.paddr)
apbDataSt pwdata_q;
`DFF_CLK(clk, pwdata_q, cpu_main.pwdata)
logic penable_q;
`DFF_CLK(clk, penable_q, cpu_main.penable)
logic pwrite_q;
`DFF_CLK(clk, pwrite_q, cpu_main.pwrite)

logic pready;
logic set_trans_active;
logic trans_active;
`SCFF_CLK(clk, trans_active, set_trans_active, pready)

//signals for interface apbReg_uBridge
logic apbReg_uBridge_psel;
logic apbReg_uBridge_next_psel;
`SCFF_CLK(clk, apbReg_uBridge_psel, apbReg_uBridge_next_psel, apbReg_uBridge.pready)

assign apbReg_uBridge.paddr   = paddr_q;
assign apbReg_uBridge.penable = penable_q & apbReg_uBridge_psel;
assign apbReg_uBridge.psel    = apbReg_uBridge_psel;
assign apbReg_uBridge.pwrite  = pwrite_q;
assign apbReg_uBridge.pwdata  = pwdata_q;

//signals for interface apbReg_uIp1
logic apbReg_uIp1_psel;
logic apbReg_uIp1_next_psel;
`SCFF_CLK(clk, apbReg_uIp1_psel, apbReg_uIp1_next_psel, apbReg_uIp1.pready)

assign apbReg_uIp1.paddr   = paddr_q;
assign apbReg_uIp1.penable = penable_q & apbReg_uIp1_psel;
assign apbReg_uIp1.psel    = apbReg_uIp1_psel;
assign apbReg_uIp1.pwrite  = pwrite_q;
assign apbReg_uIp1.pwdata  = pwdata_q;

//signals for interface apbReg_uIp0
logic apbReg_uIp0_psel;
logic apbReg_uIp0_next_psel;
`SCFF_CLK(clk, apbReg_uIp0_psel, apbReg_uIp0_next_psel, apbReg_uIp0.pready)

assign apbReg_uIp0.paddr   = paddr_q;
assign apbReg_uIp0.penable = penable_q & apbReg_uIp0_psel;
assign apbReg_uIp0.psel    = apbReg_uIp0_psel;
assign apbReg_uIp0.pwrite  = pwrite_q;
assign apbReg_uIp0.pwdata  = pwdata_q;

always_comb begin
    apbReg_uBridge_next_psel = 1'b0;
    apbReg_uIp1_next_psel = 1'b0;
    apbReg_uIp0_next_psel = 1'b0;
    set_trans_active = 1'b0;
    if (cpu_main.psel & ~trans_active) begin
        set_trans_active = 1'b1;
        if (apb_addr >= apbAddrSt'(32'h200_0000)) begin
            apbReg_uBridge_next_psel = '1;
        end else if (apb_addr >= apbAddrSt'(32'h100_0000)) begin
            apbReg_uIp1_next_psel = '1;
        end else begin
            apbReg_uIp0_next_psel = '1;
        end
    end
end

logic cpu_main_next_pready;
apbDataSt cpu_main_next_prdata, prdata;
logic cpu_main_next_pslverr, pslverr;
always_comb begin
    cpu_main_next_pready  = '0;
    cpu_main_next_prdata  = '0;
    cpu_main_next_pslverr = '0;
    if (apbReg_uBridge_psel) begin
        cpu_main_next_pready  = apbReg_uBridge.pready;
        cpu_main_next_prdata  = apbReg_uBridge.prdata;
        cpu_main_next_pslverr = apbReg_uBridge.pslverr;
    end else if (apbReg_uIp1_psel) begin
        cpu_main_next_pready  = apbReg_uIp1.pready;
        cpu_main_next_prdata  = apbReg_uIp1.prdata;
        cpu_main_next_pslverr = apbReg_uIp1.pslverr;
    end else if (apbReg_uIp0_psel) begin
        cpu_main_next_pready  = apbReg_uIp0.pready;
        cpu_main_next_prdata  = apbReg_uIp0.prdata;
        cpu_main_next_pslverr = apbReg_uIp0.pslverr;
    end
end

`DFF_CLK(clk, pready, cpu_main_next_pready)
`DFF_CLK(clk, prdata, cpu_main_next_prdata)
`DFF_CLK(clk, pslverr, cpu_main_next_pslverr)
assign cpu_main.pready  = pready;
assign cpu_main.prdata  = prdata;
assign cpu_main.pslverr = pslverr;

endmodule: ip_test_apbDecode
// GENERATED_CODE_END
