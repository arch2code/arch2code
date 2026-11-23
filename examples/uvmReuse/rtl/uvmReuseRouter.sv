//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseRouter
// GENERATED_CODE_BEGIN --template=apbDecodeModule
//module as defined by block: uvmReuseRouter
module uvmReuseRouter
// Generated Import package statement(s)
import uvmReuseLeaf_package::*;
(
    apb_if.src apbReg_uLeafA,
    apb_if.src apbReg_uLeafB,
    apb_if.dst apbReg,
    input clk, rst_n
);

uvmReuseAddrSt apb_addr;
assign apb_addr = uvmReuseAddrSt'(apbReg.paddr) & uvmReuseAddrSt'(32'h3fff);
//signals for interface apbReg
uvmReuseAddrSt paddr_q;
`DFF_DOM(clk, rst_n, paddr_q, apbReg.paddr)
uvmReuseDataSt pwdata_q;
`DFF_DOM(clk, rst_n, pwdata_q, apbReg.pwdata)
logic penable_q;
`DFF_DOM(clk, rst_n, penable_q, apbReg.penable)
logic pwrite_q;
`DFF_DOM(clk, rst_n, pwrite_q, apbReg.pwrite)

logic pready;
logic set_trans_active;
logic trans_active;
`SCFF_DOM(clk, rst_n, trans_active, set_trans_active, pready)

//signals for interface apbReg_uLeafB
logic apbReg_uLeafB_psel;
logic apbReg_uLeafB_next_psel;
`SCFF_DOM(clk, rst_n, apbReg_uLeafB_psel, apbReg_uLeafB_next_psel, apbReg_uLeafB.pready)

assign apbReg_uLeafB.paddr   = paddr_q;
assign apbReg_uLeafB.penable = penable_q & apbReg_uLeafB_psel;
assign apbReg_uLeafB.psel    = apbReg_uLeafB_psel;
assign apbReg_uLeafB.pwrite  = pwrite_q;
assign apbReg_uLeafB.pwdata  = pwdata_q;

//signals for interface apbReg_uLeafA
logic apbReg_uLeafA_psel;
logic apbReg_uLeafA_next_psel;
`SCFF_DOM(clk, rst_n, apbReg_uLeafA_psel, apbReg_uLeafA_next_psel, apbReg_uLeafA.pready)

assign apbReg_uLeafA.paddr   = paddr_q;
assign apbReg_uLeafA.penable = penable_q & apbReg_uLeafA_psel;
assign apbReg_uLeafA.psel    = apbReg_uLeafA_psel;
assign apbReg_uLeafA.pwrite  = pwrite_q;
assign apbReg_uLeafA.pwdata  = pwdata_q;

always_comb begin
    apbReg_uLeafB_next_psel = 1'b0;
    apbReg_uLeafA_next_psel = 1'b0;
    set_trans_active = 1'b0;
    if (apbReg.psel & ~trans_active) begin
        set_trans_active = 1'b1;
        if (apb_addr >= uvmReuseAddrSt'(32'h2000)) begin
            // unmapped, selects no child
        end else if (apb_addr >= uvmReuseAddrSt'(32'h1000)) begin
            apbReg_uLeafB_next_psel = '1;
        end else begin
            apbReg_uLeafA_next_psel = '1;
        end
    end
end

logic apbReg_next_pready;
uvmReuseDataSt apbReg_next_prdata, prdata;
logic apbReg_next_pslverr, pslverr;
always_comb begin
    apbReg_next_pready  = '0;
    apbReg_next_prdata  = '0;
    apbReg_next_pslverr = '0;
    if (apbReg_uLeafB_psel) begin
        apbReg_next_pready  = apbReg_uLeafB.pready;
        apbReg_next_prdata  = apbReg_uLeafB.prdata;
        apbReg_next_pslverr = apbReg_uLeafB.pslverr;
    end else if (apbReg_uLeafA_psel) begin
        apbReg_next_pready  = apbReg_uLeafA.pready;
        apbReg_next_prdata  = apbReg_uLeafA.prdata;
        apbReg_next_pslverr = apbReg_uLeafA.pslverr;
    end else if (trans_active & ~pready) begin
        apbReg_next_pready  = 1'b1;
        apbReg_next_prdata  = uvmReuseDataSt'(32'hBADD_C0DE);
    end
end

`DFF_DOM(clk, rst_n, pready, apbReg_next_pready)
`DFF_DOM(clk, rst_n, prdata, apbReg_next_prdata)
`DFF_DOM(clk, rst_n, pslverr, apbReg_next_pslverr)
assign apbReg.pready  = pready;
assign apbReg.prdata  = prdata;
assign apbReg.pslverr = pslverr;

endmodule: uvmReuseRouter
// GENERATED_CODE_END
