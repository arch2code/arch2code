// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: apbDecode
module apbDecode
// Generated Import package statement(s)
import mixed_package::*;
(
    apb_if.src apb_uBlockA,
    apb_if.src apb_uBlockB,
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

//signals for interface apb_uBlockB
logic apb_uBlockB_psel;
logic apb_uBlockB_next_psel;
`SCFF(apb_uBlockB_psel, apb_uBlockB_next_psel, apb_uBlockB.pready)

assign apb_uBlockB.paddr   = paddr_q;
assign apb_uBlockB.penable = penable_q & apb_uBlockB_psel;
assign apb_uBlockB.psel    = apb_uBlockB_psel;
assign apb_uBlockB.pwrite  = pwrite_q;
assign apb_uBlockB.pwdata  = pwdata_q;

//signals for interface apb_uBlockA
logic apb_uBlockA_psel;
logic apb_uBlockA_next_psel;
`SCFF(apb_uBlockA_psel, apb_uBlockA_next_psel, apb_uBlockA.pready)

assign apb_uBlockA.paddr   = paddr_q;
assign apb_uBlockA.penable = penable_q & apb_uBlockA_psel;
assign apb_uBlockA.psel    = apb_uBlockA_psel;
assign apb_uBlockA.pwrite  = pwrite_q;
assign apb_uBlockA.pwdata  = pwdata_q;

always_comb begin
    apb_uBlockB_next_psel = 1'b0;
    apb_uBlockA_next_psel = 1'b0;
    set_trans_active = 1'b0;
    if (cpu_main.psel & ~trans_active) begin
        set_trans_active = 1'b1;
        if (apb_addr >= apbAddrSt'(32'h100_0000)) begin
            apb_uBlockB_next_psel = '1;
        end else begin
            apb_uBlockA_next_psel = '1;
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
    if (apb_uBlockB_psel) begin
        cpu_main_next_pready  = apb_uBlockB.pready;
        cpu_main_next_prdata  = apb_uBlockB.prdata;
        cpu_main_next_pslverr = apb_uBlockB.pslverr;
    end else if (apb_uBlockA_psel) begin
        cpu_main_next_pready  = apb_uBlockA.pready;
        cpu_main_next_prdata  = apb_uBlockA.prdata;
        cpu_main_next_pslverr = apb_uBlockA.pslverr;
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
