//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsBridgeRouter
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: uvmRegsBridgeRouter
module uvmRegsBridgeRouter
// Generated Import package statement(s)
import uvmRegs_package::*;
(
    apb_if.src apbReg_uDeep,
    apb_if.dst apbReg,
    input clk, rst_n
);

uvmRegsAddrSt apb_addr;
assign apb_addr = uvmRegsAddrSt'(apbReg.paddr) & uvmRegsAddrSt'(32'h3ff);
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

//signals for interface apbReg_uDeep
logic apbReg_uDeep_psel;
logic apbReg_uDeep_next_psel;
`SCFF_DOM(clk, rst_n, apbReg_uDeep_psel, apbReg_uDeep_next_psel, apbReg_uDeep.pready)

assign apbReg_uDeep.paddr   = paddr_q;
assign apbReg_uDeep.penable = penable_q & apbReg_uDeep_psel;
assign apbReg_uDeep.psel    = apbReg_uDeep_psel;
assign apbReg_uDeep.pwrite  = pwrite_q;
assign apbReg_uDeep.pwdata  = pwdata_q;

always_comb begin
    apbReg_uDeep_next_psel = 1'b0;
    set_trans_active = 1'b0;
    if (apbReg.psel & ~trans_active) begin
        set_trans_active = 1'b1;
        if (apb_addr >= uvmRegsAddrSt'(32'h100)) begin
            // unmapped, selects no child
        end else begin
            apbReg_uDeep_next_psel = '1;
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
    if (apbReg_uDeep_psel) begin
        apbReg_next_pready  = apbReg_uDeep.pready;
        apbReg_next_prdata  = apbReg_uDeep.prdata;
        apbReg_next_pslverr = apbReg_uDeep.pslverr;
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

endmodule: uvmRegsBridgeRouter
// GENERATED_CODE_END
