//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdDecode
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: ip_ipStdDecode
module ip_ipStdDecode
// Generated Import package statement(s)
import ip_package::*;
(
    apb_if.dst ipReg,
    apb_if.src ipReg_uIp,
    input clk, rst_n
);

ipRegAddrSt apb_addr;
assign apb_addr = ipRegAddrSt'(ipReg.paddr) & ipRegAddrSt'(32'hfff_ffff);
//signals for interface ipReg
ipRegAddrSt paddr_q;
`DFF (paddr_q, ipReg.paddr)
ipRegDataSt pwdata_q;
`DFF (pwdata_q, ipReg.pwdata)
logic penable_q;
`DFF (penable_q, ipReg.penable)
logic pwrite_q;
`DFF (pwrite_q, ipReg.pwrite)

logic pready;
logic set_trans_active;
logic trans_active;
`SCFF(trans_active, set_trans_active, pready)

//signals for interface ipReg_uIp
logic ipReg_uIp_psel;
logic ipReg_uIp_next_psel;
`SCFF(ipReg_uIp_psel, ipReg_uIp_next_psel, ipReg_uIp.pready)

assign ipReg_uIp.paddr   = paddr_q;
assign ipReg_uIp.penable = penable_q & ipReg_uIp_psel;
assign ipReg_uIp.psel    = ipReg_uIp_psel;
assign ipReg_uIp.pwrite  = pwrite_q;
assign ipReg_uIp.pwdata  = pwdata_q;

always_comb begin
    ipReg_uIp_next_psel = 1'b0;
    set_trans_active = 1'b0;
    if (ipReg.psel & ~trans_active) begin
        set_trans_active = 1'b1;
        ipReg_uIp_next_psel = '1;
    end
end

logic ipReg_next_pready;
ipRegDataSt ipReg_next_prdata, prdata;
logic ipReg_next_pslverr, pslverr;
always_comb begin
    ipReg_next_pready  = '0;
    ipReg_next_prdata  = '0;
    ipReg_next_pslverr = '0;
    if (ipReg_uIp_psel) begin
        ipReg_next_pready  = ipReg_uIp.pready;
        ipReg_next_prdata  = ipReg_uIp.prdata;
        ipReg_next_pslverr = ipReg_uIp.pslverr;
    end
end

`DFF(pready, ipReg_next_pready)
`DFF(prdata, ipReg_next_prdata)
`DFF(pslverr, ipReg_next_pslverr)
assign ipReg.pready  = pready;
assign ipReg.prdata  = prdata;
assign ipReg.pslverr = pslverr;

endmodule: ip_ipStdDecode
// GENERATED_CODE_END
