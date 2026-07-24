//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: apbDecode
module apbDecode
// Generated Import package statement(s)
import shared_types_package::*;
(
    apb_if.src apbReg_uIp,
    apb_if.dst cpu_main,
    input clk, rst_n
);

apbAddrSt apb_addr;
assign apb_addr = apbAddrSt'(cpu_main.paddr) & apbAddrSt'(32'hfff_ffff);
//signals for interface cpu_main
apbAddrSt paddr_q;
`DFF (paddr_q, cpu_main.paddr)
apbDataSt pwdata_q;
`DFF (pwdata_q, cpu_main.pwdata)
logic penable_q;
`DFF (penable_q, cpu_main.penable)
logic pwrite_q;
`DFF (pwrite_q, cpu_main.pwrite)

logic pready;
logic set_trans_active;
logic trans_active;
`SCFF(trans_active, set_trans_active, pready)

//signals for interface apbReg_uIp
logic apbReg_uIp_psel;
logic apbReg_uIp_next_psel;
`SCFF(apbReg_uIp_psel, apbReg_uIp_next_psel, apbReg_uIp.pready)

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

`DFF(pready, cpu_main_next_pready)
`DFF(prdata, cpu_main_next_prdata)
`DFF(pslverr, cpu_main_next_pslverr)
assign cpu_main.pready  = pready;
assign cpu_main.prdata  = prdata;
assign cpu_main.pslverr = pslverr;

endmodule: apbDecode
// GENERATED_CODE_END
