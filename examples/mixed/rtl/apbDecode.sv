// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: mixed_apbDecode
module mixed_apbDecode
// Generated Import package statement(s)
import mixed_package::*;
(
    apb_if.src apbReg_uBlockA,
    apb_if.src apbReg_uBlockB,
    apb_if.src apbReg_uBlockG,
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

//signals for interface apbReg_uBlockG
logic apbReg_uBlockG_psel;
logic apbReg_uBlockG_next_psel;
`SCFF_CLK(clk, apbReg_uBlockG_psel, apbReg_uBlockG_next_psel, apbReg_uBlockG.pready)

assign apbReg_uBlockG.paddr   = paddr_q;
assign apbReg_uBlockG.penable = penable_q & apbReg_uBlockG_psel;
assign apbReg_uBlockG.psel    = apbReg_uBlockG_psel;
assign apbReg_uBlockG.pwrite  = pwrite_q;
assign apbReg_uBlockG.pwdata  = pwdata_q;

//signals for interface apbReg_uBlockB
logic apbReg_uBlockB_psel;
logic apbReg_uBlockB_next_psel;
`SCFF_CLK(clk, apbReg_uBlockB_psel, apbReg_uBlockB_next_psel, apbReg_uBlockB.pready)

assign apbReg_uBlockB.paddr   = paddr_q;
assign apbReg_uBlockB.penable = penable_q & apbReg_uBlockB_psel;
assign apbReg_uBlockB.psel    = apbReg_uBlockB_psel;
assign apbReg_uBlockB.pwrite  = pwrite_q;
assign apbReg_uBlockB.pwdata  = pwdata_q;

//signals for interface apbReg_uBlockA
logic apbReg_uBlockA_psel;
logic apbReg_uBlockA_next_psel;
`SCFF_CLK(clk, apbReg_uBlockA_psel, apbReg_uBlockA_next_psel, apbReg_uBlockA.pready)

assign apbReg_uBlockA.paddr   = paddr_q;
assign apbReg_uBlockA.penable = penable_q & apbReg_uBlockA_psel;
assign apbReg_uBlockA.psel    = apbReg_uBlockA_psel;
assign apbReg_uBlockA.pwrite  = pwrite_q;
assign apbReg_uBlockA.pwdata  = pwdata_q;

always_comb begin
    apbReg_uBlockG_next_psel = 1'b0;
    apbReg_uBlockB_next_psel = 1'b0;
    apbReg_uBlockA_next_psel = 1'b0;
    set_trans_active = 1'b0;
    if (cpu_main.psel & ~trans_active) begin
        set_trans_active = 1'b1;
        if (apb_addr >= apbAddrSt'(32'h200_0000)) begin
            apbReg_uBlockG_next_psel = '1;
        end else if (apb_addr >= apbAddrSt'(32'h100_0000)) begin
            apbReg_uBlockB_next_psel = '1;
        end else begin
            apbReg_uBlockA_next_psel = '1;
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
    if (apbReg_uBlockG_psel) begin
        cpu_main_next_pready  = apbReg_uBlockG.pready;
        cpu_main_next_prdata  = apbReg_uBlockG.prdata;
        cpu_main_next_pslverr = apbReg_uBlockG.pslverr;
    end else if (apbReg_uBlockB_psel) begin
        cpu_main_next_pready  = apbReg_uBlockB.pready;
        cpu_main_next_prdata  = apbReg_uBlockB.prdata;
        cpu_main_next_pslverr = apbReg_uBlockB.pslverr;
    end else if (apbReg_uBlockA_psel) begin
        cpu_main_next_pready  = apbReg_uBlockA.pready;
        cpu_main_next_prdata  = apbReg_uBlockA.prdata;
        cpu_main_next_pslverr = apbReg_uBlockA.pslverr;
    end
end

`DFF_CLK(clk, pready, cpu_main_next_pready)
`DFF_CLK(clk, prdata, cpu_main_next_prdata)
`DFF_CLK(clk, pslverr, cpu_main_next_pslverr)
assign cpu_main.pready  = pready;
assign cpu_main.prdata  = prdata;
assign cpu_main.pslverr = pslverr;

endmodule: mixed_apbDecode
// GENERATED_CODE_END
