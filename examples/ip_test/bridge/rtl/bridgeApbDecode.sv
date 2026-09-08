//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeApbDecode
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: ipBridge_bridgeApbDecode
module ipBridge_bridgeApbDecode
// Generated Import package statement(s)
import common_shared_types_package::*;
(
    apb_if.src apbReg_uBridgeIp0,
    apb_if.src apbReg_uBridgeIp1,
    apb_if.dst apbReg,
    input clk, rst_n
);

apbAddrSt apb_addr;
assign apb_addr = apbAddrSt'(apbReg.paddr) & apbAddrSt'(32'hff_ffff);
//signals for interface apbReg
apbAddrSt paddr_q;
`DFF_CLK(clk, paddr_q, apbReg.paddr)
apbDataSt pwdata_q;
`DFF_CLK(clk, pwdata_q, apbReg.pwdata)
logic penable_q;
`DFF_CLK(clk, penable_q, apbReg.penable)
logic pwrite_q;
`DFF_CLK(clk, pwrite_q, apbReg.pwrite)

logic pready;
logic set_trans_active;
logic trans_active;
`SCFF_CLK(clk, trans_active, set_trans_active, pready)

//signals for interface apbReg_uBridgeIp1
logic apbReg_uBridgeIp1_psel;
logic apbReg_uBridgeIp1_next_psel;
`SCFF_CLK(clk, apbReg_uBridgeIp1_psel, apbReg_uBridgeIp1_next_psel, apbReg_uBridgeIp1.pready)

assign apbReg_uBridgeIp1.paddr   = paddr_q;
assign apbReg_uBridgeIp1.penable = penable_q & apbReg_uBridgeIp1_psel;
assign apbReg_uBridgeIp1.psel    = apbReg_uBridgeIp1_psel;
assign apbReg_uBridgeIp1.pwrite  = pwrite_q;
assign apbReg_uBridgeIp1.pwdata  = pwdata_q;

//signals for interface apbReg_uBridgeIp0
logic apbReg_uBridgeIp0_psel;
logic apbReg_uBridgeIp0_next_psel;
`SCFF_CLK(clk, apbReg_uBridgeIp0_psel, apbReg_uBridgeIp0_next_psel, apbReg_uBridgeIp0.pready)

assign apbReg_uBridgeIp0.paddr   = paddr_q;
assign apbReg_uBridgeIp0.penable = penable_q & apbReg_uBridgeIp0_psel;
assign apbReg_uBridgeIp0.psel    = apbReg_uBridgeIp0_psel;
assign apbReg_uBridgeIp0.pwrite  = pwrite_q;
assign apbReg_uBridgeIp0.pwdata  = pwdata_q;

always_comb begin
    apbReg_uBridgeIp1_next_psel = 1'b0;
    apbReg_uBridgeIp0_next_psel = 1'b0;
    set_trans_active = 1'b0;
    if (apbReg.psel & ~trans_active) begin
        set_trans_active = 1'b1;
        if (apb_addr >= apbAddrSt'(32'h10_0000)) begin
            apbReg_uBridgeIp1_next_psel = '1;
        end else begin
            apbReg_uBridgeIp0_next_psel = '1;
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
    if (apbReg_uBridgeIp1_psel) begin
        apbReg_next_pready  = apbReg_uBridgeIp1.pready;
        apbReg_next_prdata  = apbReg_uBridgeIp1.prdata;
        apbReg_next_pslverr = apbReg_uBridgeIp1.pslverr;
    end else if (apbReg_uBridgeIp0_psel) begin
        apbReg_next_pready  = apbReg_uBridgeIp0.pready;
        apbReg_next_prdata  = apbReg_uBridgeIp0.prdata;
        apbReg_next_pslverr = apbReg_uBridgeIp0.pslverr;
    end
end

`DFF_CLK(clk, pready, apbReg_next_pready)
`DFF_CLK(clk, prdata, apbReg_next_prdata)
`DFF_CLK(clk, pslverr, apbReg_next_pslverr)
assign apbReg.pready  = pready;
assign apbReg.prdata  = prdata;
assign apbReg.pslverr = pslverr;

endmodule: ipBridge_bridgeApbDecode
// GENERATED_CODE_END
