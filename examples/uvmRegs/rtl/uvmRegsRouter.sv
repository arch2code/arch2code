//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsRouter
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: uvmRegsRouter
module uvmRegsRouter
// Generated Import package statement(s)
import uvmRegs_package::*;
(
    apb_if.src apbReg_uScale0,
    apb_if.src apbReg_uScale1,
    apb_if.src apbReg_uStat,
    apb_if.src apbReg_uWrap,
    apb_if.src apbReg_uBridge,
    apb_if.dst apbReg,
    input clk, rst_n
);

uvmRegsAddrSt apb_addr;
assign apb_addr = uvmRegsAddrSt'(apbReg.paddr) & uvmRegsAddrSt'(32'h7fff);
//signals for interface apbReg
uvmRegsAddrSt paddr_q;
`DFF_DOM(clk, rst_n, paddr_q, apbReg.paddr)
uvmRegsDataSt pwdata_q;
`DFF_DOM(clk, rst_n, pwdata_q, apbReg.pwdata)
logic penable_q;
`DFF_DOM(clk, rst_n, penable_q, apbReg.penable)
logic pwrite_q;
`DFF_DOM(clk, rst_n, pwrite_q, apbReg.pwrite)

logic pready;
logic set_trans_active;
logic trans_active;
`SCFF_DOM(clk, rst_n, trans_active, set_trans_active, pready)

//signals for interface apbReg_uWrap
logic apbReg_uWrap_psel;
logic apbReg_uWrap_next_psel;
`SCFF_DOM(clk, rst_n, apbReg_uWrap_psel, apbReg_uWrap_next_psel, apbReg_uWrap.pready)

assign apbReg_uWrap.paddr   = paddr_q;
assign apbReg_uWrap.penable = penable_q & apbReg_uWrap_psel;
assign apbReg_uWrap.psel    = apbReg_uWrap_psel;
assign apbReg_uWrap.pwrite  = pwrite_q;
assign apbReg_uWrap.pwdata  = pwdata_q;

//signals for interface apbReg_uBridge
logic apbReg_uBridge_psel;
logic apbReg_uBridge_next_psel;
`SCFF_DOM(clk, rst_n, apbReg_uBridge_psel, apbReg_uBridge_next_psel, apbReg_uBridge.pready)

assign apbReg_uBridge.paddr   = paddr_q;
assign apbReg_uBridge.penable = penable_q & apbReg_uBridge_psel;
assign apbReg_uBridge.psel    = apbReg_uBridge_psel;
assign apbReg_uBridge.pwrite  = pwrite_q;
assign apbReg_uBridge.pwdata  = pwdata_q;

//signals for interface apbReg_uStat
logic apbReg_uStat_psel;
logic apbReg_uStat_next_psel;
`SCFF_DOM(clk, rst_n, apbReg_uStat_psel, apbReg_uStat_next_psel, apbReg_uStat.pready)

assign apbReg_uStat.paddr   = paddr_q;
assign apbReg_uStat.penable = penable_q & apbReg_uStat_psel;
assign apbReg_uStat.psel    = apbReg_uStat_psel;
assign apbReg_uStat.pwrite  = pwrite_q;
assign apbReg_uStat.pwdata  = pwdata_q;

//signals for interface apbReg_uScale1
logic apbReg_uScale1_psel;
logic apbReg_uScale1_next_psel;
`SCFF_DOM(clk, rst_n, apbReg_uScale1_psel, apbReg_uScale1_next_psel, apbReg_uScale1.pready)

assign apbReg_uScale1.paddr   = paddr_q;
assign apbReg_uScale1.penable = penable_q & apbReg_uScale1_psel;
assign apbReg_uScale1.psel    = apbReg_uScale1_psel;
assign apbReg_uScale1.pwrite  = pwrite_q;
assign apbReg_uScale1.pwdata  = pwdata_q;

//signals for interface apbReg_uScale0
logic apbReg_uScale0_psel;
logic apbReg_uScale0_next_psel;
`SCFF_DOM(clk, rst_n, apbReg_uScale0_psel, apbReg_uScale0_next_psel, apbReg_uScale0.pready)

assign apbReg_uScale0.paddr   = paddr_q;
assign apbReg_uScale0.penable = penable_q & apbReg_uScale0_psel;
assign apbReg_uScale0.psel    = apbReg_uScale0_psel;
assign apbReg_uScale0.pwrite  = pwrite_q;
assign apbReg_uScale0.pwdata  = pwdata_q;

always_comb begin
    apbReg_uWrap_next_psel = 1'b0;
    apbReg_uBridge_next_psel = 1'b0;
    apbReg_uStat_next_psel = 1'b0;
    apbReg_uScale1_next_psel = 1'b0;
    apbReg_uScale0_next_psel = 1'b0;
    set_trans_active = 1'b0;
    if (apbReg.psel & ~trans_active) begin
        set_trans_active = 1'b1;
        if (apb_addr >= uvmRegsAddrSt'(32'h6000)) begin
            // unmapped, selects no child
        end else if (apb_addr >= uvmRegsAddrSt'(32'h5000)) begin
            apbReg_uWrap_next_psel = '1;
        end else if (apb_addr >= uvmRegsAddrSt'(32'h4000)) begin
            apbReg_uBridge_next_psel = '1;
        end else if (apb_addr >= uvmRegsAddrSt'(32'h3000)) begin
            apbReg_uStat_next_psel = '1;
        end else if (apb_addr >= uvmRegsAddrSt'(32'h1000)) begin
            apbReg_uScale1_next_psel = '1;
        end else begin
            apbReg_uScale0_next_psel = '1;
        end
    end
end

logic apbReg_next_pready;
uvmRegsDataSt apbReg_next_prdata, prdata;
logic apbReg_next_pslverr, pslverr;
always_comb begin
    apbReg_next_pready  = '0;
    apbReg_next_prdata  = '0;
    apbReg_next_pslverr = '0;
    if (apbReg_uWrap_psel) begin
        apbReg_next_pready  = apbReg_uWrap.pready;
        apbReg_next_prdata  = apbReg_uWrap.prdata;
        apbReg_next_pslverr = apbReg_uWrap.pslverr;
    end else if (apbReg_uBridge_psel) begin
        apbReg_next_pready  = apbReg_uBridge.pready;
        apbReg_next_prdata  = apbReg_uBridge.prdata;
        apbReg_next_pslverr = apbReg_uBridge.pslverr;
    end else if (apbReg_uStat_psel) begin
        apbReg_next_pready  = apbReg_uStat.pready;
        apbReg_next_prdata  = apbReg_uStat.prdata;
        apbReg_next_pslverr = apbReg_uStat.pslverr;
    end else if (apbReg_uScale1_psel) begin
        apbReg_next_pready  = apbReg_uScale1.pready;
        apbReg_next_prdata  = apbReg_uScale1.prdata;
        apbReg_next_pslverr = apbReg_uScale1.pslverr;
    end else if (apbReg_uScale0_psel) begin
        apbReg_next_pready  = apbReg_uScale0.pready;
        apbReg_next_prdata  = apbReg_uScale0.prdata;
        apbReg_next_pslverr = apbReg_uScale0.pslverr;
    end else if (trans_active & ~pready) begin
        apbReg_next_pready  = 1'b1;
        apbReg_next_prdata  = uvmRegsDataSt'(32'hBADD_C0DE);
    end
end

`DFF_DOM(clk, rst_n, pready, apbReg_next_pready)
`DFF_DOM(clk, rst_n, prdata, apbReg_next_prdata)
`DFF_DOM(clk, rst_n, pslverr, apbReg_next_pslverr)
assign apbReg.pready  = pready;
assign apbReg.prdata  = prdata;
assign apbReg.pslverr = pslverr;

endmodule: uvmRegsRouter
// GENERATED_CODE_END
