// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: apbDecode
module apbDecode
// Generated Import package statement(s)
import apbDecode_package::*;
(
    apb_if.src apbReg_uBlockA,
    apb_if.src apbReg_uBlockB,
    apb_if.dst apbReg,
    input clk, rst_n
);

apbAddrSt apb_addr;
assign apb_addr = apbAddrSt'(apbReg.paddr) & apbAddrSt'(32'hfff_ffff);
//signals for interface apbReg
apbAddrSt paddr_q;
`DFF (paddr_q, apbReg.paddr)
apbDataSt pwdata_q;
`DFF (pwdata_q, apbReg.pwdata)
logic penable_q;
`DFF (penable_q, apbReg.penable)
logic pwrite_q;
`DFF (pwrite_q, apbReg.pwrite)

logic pready;
logic set_trans_active;
logic trans_active;
`SCFF(trans_active, set_trans_active, pready)

//signals for interface apbReg_uBlockB
logic apbReg_uBlockB_psel;
logic apbReg_uBlockB_next_psel;
`SCFF(apbReg_uBlockB_psel, apbReg_uBlockB_next_psel, apbReg_uBlockB.pready)

assign apbReg_uBlockB.paddr   = paddr_q;
assign apbReg_uBlockB.penable = penable_q & apbReg_uBlockB_psel;
assign apbReg_uBlockB.psel    = apbReg_uBlockB_psel;
assign apbReg_uBlockB.pwrite  = pwrite_q;
assign apbReg_uBlockB.pwdata  = pwdata_q;

//signals for interface apbReg_uBlockA
logic apbReg_uBlockA_psel;
logic apbReg_uBlockA_next_psel;
`SCFF(apbReg_uBlockA_psel, apbReg_uBlockA_next_psel, apbReg_uBlockA.pready)

assign apbReg_uBlockA.paddr   = paddr_q;
assign apbReg_uBlockA.penable = penable_q & apbReg_uBlockA_psel;
assign apbReg_uBlockA.psel    = apbReg_uBlockA_psel;
assign apbReg_uBlockA.pwrite  = pwrite_q;
assign apbReg_uBlockA.pwdata  = pwdata_q;

always_comb begin
    apbReg_uBlockB_next_psel = 1'b0;
    apbReg_uBlockA_next_psel = 1'b0;
    set_trans_active = 1'b0;
    if (apbReg.psel & ~trans_active) begin
        set_trans_active = 1'b1;
        if (apb_addr >= apbAddrSt'(32'h100_0000)) begin
            apbReg_uBlockB_next_psel = '1;
        end else begin
            apbReg_uBlockA_next_psel = '1;
        end
    end
end

logic apbReg_next_pready;
apbDataSt apbReg_next_prdata, prdata;
logic apbReg_next_pslverr, pslverr;
always_comb begin
    apbReg_next_pready  = '0;
    apbReg_next_prdata  = '0;
    apbReg_next_pslverr = '0;
    if (apbReg_uBlockB_psel) begin
        apbReg_next_pready  = apbReg_uBlockB.pready;
        apbReg_next_prdata  = apbReg_uBlockB.prdata;
        apbReg_next_pslverr = apbReg_uBlockB.pslverr;
    end else if (apbReg_uBlockA_psel) begin
        apbReg_next_pready  = apbReg_uBlockA.pready;
        apbReg_next_prdata  = apbReg_uBlockA.prdata;
        apbReg_next_pslverr = apbReg_uBlockA.pslverr;
    end
end

`DFF(pready, apbReg_next_pready)
`DFF(prdata, apbReg_next_prdata)
`DFF(pslverr, apbReg_next_pslverr)
assign apbReg.pready  = pready;
assign apbReg.prdata  = prdata;
assign apbReg.pslverr = pslverr;

endmodule: apbDecode
// GENERATED_CODE_END
