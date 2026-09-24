//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkDecode
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: twoClk_twoClkDecode
module twoClk_twoClkDecode
// Generated Import package statement(s)
import twoClk_package::*;
(
    apb_if.src twoClkReg_uTable,
    apb_if.dst twoClkReg,
    input clk, rst_n
);

twoClkRegAddrSt apb_addr;
assign apb_addr = twoClkRegAddrSt'(twoClkReg.paddr) & twoClkRegAddrSt'(32'h3_ffff);
//signals for interface twoClkReg
twoClkRegAddrSt paddr_q;
`DFF_DOM(clk, rst_n, paddr_q, twoClkReg.paddr)
twoClkRegDataSt pwdata_q;
`DFF_DOM(clk, rst_n, pwdata_q, twoClkReg.pwdata)
logic penable_q;
`DFF_DOM(clk, rst_n, penable_q, twoClkReg.penable)
logic pwrite_q;
`DFF_DOM(clk, rst_n, pwrite_q, twoClkReg.pwrite)

logic pready;
logic set_trans_active;
logic trans_active;
`SCFF_DOM(clk, rst_n, trans_active, set_trans_active, pready)

//signals for interface twoClkReg_uTable
logic twoClkReg_uTable_psel;
logic twoClkReg_uTable_next_psel;
`SCFF_DOM(clk, rst_n, twoClkReg_uTable_psel, twoClkReg_uTable_next_psel, twoClkReg_uTable.pready)

assign twoClkReg_uTable.paddr   = paddr_q;
assign twoClkReg_uTable.penable = penable_q & twoClkReg_uTable_psel;
assign twoClkReg_uTable.psel    = twoClkReg_uTable_psel;
assign twoClkReg_uTable.pwrite  = pwrite_q;
assign twoClkReg_uTable.pwdata  = pwdata_q;

always_comb begin
    twoClkReg_uTable_next_psel = 1'b0;
    set_trans_active = 1'b0;
    if (twoClkReg.psel & ~trans_active) begin
        set_trans_active = 1'b1;
        begin
            twoClkReg_uTable_next_psel = '1;
        end
    end
end

logic twoClkReg_next_pready;
twoClkRegDataSt twoClkReg_next_prdata, prdata;
logic twoClkReg_next_pslverr, pslverr;
always_comb begin
    twoClkReg_next_pready  = '0;
    twoClkReg_next_prdata  = '0;
    twoClkReg_next_pslverr = '0;
    if (twoClkReg_uTable_psel) begin
        twoClkReg_next_pready  = twoClkReg_uTable.pready;
        twoClkReg_next_prdata  = twoClkReg_uTable.prdata;
        twoClkReg_next_pslverr = twoClkReg_uTable.pslverr;
    end
end

`DFF_DOM(clk, rst_n, pready, twoClkReg_next_pready)
`DFF_DOM(clk, rst_n, prdata, twoClkReg_next_prdata)
`DFF_DOM(clk, rst_n, pslverr, twoClkReg_next_pslverr)
assign twoClkReg.pready  = pready;
assign twoClkReg.prdata  = prdata;
assign twoClkReg.pslverr = pslverr;

endmodule: twoClk_twoClkDecode
// GENERATED_CODE_END
