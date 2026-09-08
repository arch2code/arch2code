//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: simple_ip_apbDecode
module simple_ip_apbDecode
// Generated Import package statement(s)
import common_shared_types_package::*;
(
    apb_if.src apbReg_uIp,
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

//signals for interface apbReg_uIp
logic apbReg_uIp_psel;
logic apbReg_uIp_next_psel;
`SCFF_CLK(clk, apbReg_uIp_psel, apbReg_uIp_next_psel, apbReg_uIp.pready)

assign apbReg_uIp.paddr   = paddr_q;
assign apbReg_uIp.penable = penable_q & apbReg_uIp_psel;
assign apbReg_uIp.psel    = apbReg_uIp_psel;
assign apbReg_uIp.pwrite  = pwrite_q;
assign apbReg_uIp.pwdata  = pwdata_q;

always_comb begin
    apbReg_uIp_next_psel = 1'b0;
    set_trans_active = 1'b0;
    if (cpu_main.psel & ~trans_active) begin
        set_trans_active = 1'b1;
        if (apb_addr >= apbAddrSt'(32'h0)) begin
            apbReg_uIp_next_psel = '1;
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
    if (apbReg_uIp_psel) begin
        cpu_main_next_pready  = apbReg_uIp.pready;
        cpu_main_next_prdata  = apbReg_uIp.prdata;
        cpu_main_next_pslverr = apbReg_uIp.pslverr;
    end
end

`DFF_CLK(clk, pready, cpu_main_next_pready)
`DFF_CLK(clk, prdata, cpu_main_next_prdata)
`DFF_CLK(clk, pslverr, cpu_main_next_pslverr)
assign cpu_main.pready  = pready;
assign cpu_main.prdata  = prdata;
assign cpu_main.pslverr = pslverr;

endmodule: simple_ip_apbDecode
// GENERATED_CODE_END
