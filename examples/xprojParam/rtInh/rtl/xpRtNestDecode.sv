//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtNestDecode
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: xpRtInh_xpRtNestDecode
module xpRtInh_xpRtNestDecode
// Generated Import package statement(s)
import xpRtInh_package::*;
import common_shared_types_package::*;
#(
    parameter RT_WIDTH
)
(
    apb_if.src apbReg_uLeaf,
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Module-local parameterizable type/struct declarations
    typedef logic[RT_WIDTH-1:0] cfgDataT; //xpRtLeaf configuration payload
    typedef struct packed {
        cfgDataT value; //xpRtLeaf configuration value
    } cfgSt;

apbAddrSt apb_addr;
assign apb_addr = apbAddrSt'(apbReg.paddr) & apbAddrSt'(32'hff_ffff);
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

//signals for interface apbReg_uLeaf
logic apbReg_uLeaf_psel;
logic apbReg_uLeaf_next_psel;
`SCFF(apbReg_uLeaf_psel, apbReg_uLeaf_next_psel, apbReg_uLeaf.pready)

assign apbReg_uLeaf.paddr   = paddr_q;
assign apbReg_uLeaf.penable = penable_q & apbReg_uLeaf_psel;
assign apbReg_uLeaf.psel    = apbReg_uLeaf_psel;
assign apbReg_uLeaf.pwrite  = pwrite_q;
assign apbReg_uLeaf.pwdata  = pwdata_q;

always_comb begin
    apbReg_uLeaf_next_psel = 1'b0;
    set_trans_active = 1'b0;
    if (apbReg.psel & ~trans_active) begin
        set_trans_active = 1'b1;
        apbReg_uLeaf_next_psel = '1;
    end
end

logic apbReg_next_pready;
apbDataSt apbReg_next_prdata, prdata;
logic apbReg_next_pslverr, pslverr;
always_comb begin
    apbReg_next_pready  = '0;
    apbReg_next_prdata  = '0;
    apbReg_next_pslverr = '0;
    if (apbReg_uLeaf_psel) begin
        apbReg_next_pready  = apbReg_uLeaf.pready;
        apbReg_next_prdata  = apbReg_uLeaf.prdata;
        apbReg_next_pslverr = apbReg_uLeaf.pslverr;
    end
end

`DFF(pready, apbReg_next_pready)
`DFF(prdata, apbReg_next_prdata)
`DFF(pslverr, apbReg_next_pslverr)
assign apbReg.pready  = pready;
assign apbReg.prdata  = prdata;
assign apbReg.pslverr = pslverr;

endmodule: xpRtInh_xpRtNestDecode
// GENERATED_CODE_END
