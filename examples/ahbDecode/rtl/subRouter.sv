//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subRouter
// GENERATED_CODE_BEGIN --template=regBusDecodeModule
//module as defined by block: subRouter
module subRouter
// Generated Import package statement(s)
import ahbDecode_package::*;
(
    ahb_if.src ahbReg_uLeafC,
    ahb_if.dst ahbReg,
    input clk, rst_n
);

ahbAddrSt ahb_addr;
assign ahb_addr = ahbAddrSt'(ahbReg.haddr) & ahbAddrSt'(32'h3ff);
//signals for interface ahbReg
logic ahb_accept;
logic ahb_dphase;
ahbAddrSt haddr_q;
`DFFEN_DOM(clk, rst_n, haddr_q, ahbReg.haddr, ahb_accept)
logic hwrite_q;
`DFFEN_DOM(clk, rst_n, hwrite_q, ahbReg.hwrite, ahb_accept)
logic [2:0] hsize_q;
`DFFEN_DOM(clk, rst_n, hsize_q, ahbReg.hsize, ahb_accept)
ahbDataSt hwdata_q;
`DFF_DOM(clk, rst_n, hwdata_q, ahbReg.hwdata)
`DFF_DOM(clk, rst_n, ahb_dphase, ahb_accept | (ahb_dphase & ~ahbReg.hreadyout))

//signals for interface ahbReg_uLeafC
logic ahbReg_uLeafC_sel;
logic ahbReg_uLeafC_next_sel;
logic ahbReg_uLeafC_aphase;
logic ahbReg_uLeafC_ready;
`DFF_DOM(clk, rst_n, ahbReg_uLeafC_aphase, ahbReg_uLeafC_next_sel)
assign ahbReg_uLeafC_ready = ahbReg_uLeafC_sel & ~ahbReg_uLeafC_aphase & ahbReg_uLeafC.hreadyout;
`SCFF_DOM(clk, rst_n, ahbReg_uLeafC_sel, ahbReg_uLeafC_next_sel, ahbReg_uLeafC_ready)

assign ahbReg_uLeafC.hsel   = ahbReg_uLeafC_aphase;
assign ahbReg_uLeafC.htrans = ahbReg_uLeafC_aphase ? 2'b10 : 2'b00;
assign ahbReg_uLeafC.haddr  = haddr_q;
assign ahbReg_uLeafC.hwrite = hwrite_q;
assign ahbReg_uLeafC.hsize  = hsize_q;
assign ahbReg_uLeafC.hwdata = hwdata_q;
assign ahbReg_uLeafC.hready = ahbReg_uLeafC.hreadyout;

always_comb begin
    ahbReg_uLeafC_next_sel = 1'b0;
    ahb_accept = 1'b0;
    if (ahbReg.hsel & ahbReg.htrans[1] & ahbReg.hready) begin
        ahb_accept = 1'b1;
        if (ahb_addr >= ahbAddrSt'(32'h100)) begin
            // unmapped, selects no child
        end else begin
            ahbReg_uLeafC_next_sel = '1;
        end
    end
end

logic ahbReg_next_hready, hready_q;
ahbDataSt ahbReg_next_hrdata, hrdata_q;
logic ahbReg_next_hresp, hresp_q;
logic ahb_err2;
always_comb begin
    ahbReg_next_hready = '0;
    ahbReg_next_hrdata = '0;
    ahbReg_next_hresp  = '0;
    if (ahbReg_uLeafC_sel) begin
        ahbReg_next_hready = ahbReg_uLeafC_ready;
        ahbReg_next_hrdata = ahbReg_uLeafC.hrdata;
        ahbReg_next_hresp  = ahbReg_uLeafC.hresp;
    end else if (ahb_dphase & ~hready_q & ~ahb_err2) begin
        ahbReg_next_hready = 1'b1;
        ahbReg_next_hrdata = ahbDataSt'(32'hBADD_C0DE);
        ahbReg_next_hresp  = 1'b1;
    end
end

`DFF_DOM(clk, rst_n, hready_q, ahbReg_next_hready)
`DFFEN_DOM(clk, rst_n, hrdata_q, ahbReg_next_hrdata, ahbReg_next_hready)
`DFF_DOM(clk, rst_n, hresp_q, ahbReg_next_hresp)
`DFF_DOM(clk, rst_n, ahb_err2, ahb_dphase & hready_q & hresp_q)
assign ahbReg.hrdata    = hrdata_q;
assign ahbReg.hreadyout = ~ahb_dphase | (hready_q & ~hresp_q) | ahb_err2;
assign ahbReg.hresp     = (hready_q & hresp_q) | ahb_err2;

endmodule: subRouter
// GENERATED_CODE_END
