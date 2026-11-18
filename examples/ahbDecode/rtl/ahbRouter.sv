//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ahbRouter
// GENERATED_CODE_BEGIN --template=regBusDecodeModule
//module as defined by block: ahbRouter
module ahbRouter
// Generated Import package statement(s)
import ahbDecode_package::*;
(
    ahb_if.src ahbReg_uLeafA,
    ahb_if.src ahbReg_uLeafB,
    ahb_if.src ahbReg_uSubSys,
    ahb_if.dst ahbReg,
    input clk, rst_n
);

ahbAddrSt ahb_addr;
assign ahb_addr = ahbAddrSt'(ahbReg.haddr) & ahbAddrSt'(32'h3fff);
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

//signals for interface ahbReg_uSubSys
logic ahbReg_uSubSys_sel;
logic ahbReg_uSubSys_next_sel;
logic ahbReg_uSubSys_aphase;
logic ahbReg_uSubSys_ready;
`DFF_DOM(clk, rst_n, ahbReg_uSubSys_aphase, ahbReg_uSubSys_next_sel)
assign ahbReg_uSubSys_ready = ahbReg_uSubSys_sel & ~ahbReg_uSubSys_aphase & ahbReg_uSubSys.hreadyout;
`SCFF_DOM(clk, rst_n, ahbReg_uSubSys_sel, ahbReg_uSubSys_next_sel, ahbReg_uSubSys_ready)

assign ahbReg_uSubSys.hsel   = ahbReg_uSubSys_aphase;
assign ahbReg_uSubSys.htrans = ahbReg_uSubSys_aphase ? 2'b10 : 2'b00;
assign ahbReg_uSubSys.haddr  = haddr_q;
assign ahbReg_uSubSys.hwrite = hwrite_q;
assign ahbReg_uSubSys.hsize  = hsize_q;
assign ahbReg_uSubSys.hwdata = hwdata_q;
assign ahbReg_uSubSys.hready = ahbReg_uSubSys.hreadyout;

//signals for interface ahbReg_uLeafB
logic ahbReg_uLeafB_sel;
logic ahbReg_uLeafB_next_sel;
logic ahbReg_uLeafB_aphase;
logic ahbReg_uLeafB_ready;
`DFF_DOM(clk, rst_n, ahbReg_uLeafB_aphase, ahbReg_uLeafB_next_sel)
assign ahbReg_uLeafB_ready = ahbReg_uLeafB_sel & ~ahbReg_uLeafB_aphase & ahbReg_uLeafB.hreadyout;
`SCFF_DOM(clk, rst_n, ahbReg_uLeafB_sel, ahbReg_uLeafB_next_sel, ahbReg_uLeafB_ready)

assign ahbReg_uLeafB.hsel   = ahbReg_uLeafB_aphase;
assign ahbReg_uLeafB.htrans = ahbReg_uLeafB_aphase ? 2'b10 : 2'b00;
assign ahbReg_uLeafB.haddr  = haddr_q;
assign ahbReg_uLeafB.hwrite = hwrite_q;
assign ahbReg_uLeafB.hsize  = hsize_q;
assign ahbReg_uLeafB.hwdata = hwdata_q;
assign ahbReg_uLeafB.hready = ahbReg_uLeafB.hreadyout;

//signals for interface ahbReg_uLeafA
logic ahbReg_uLeafA_sel;
logic ahbReg_uLeafA_next_sel;
logic ahbReg_uLeafA_aphase;
logic ahbReg_uLeafA_ready;
`DFF_DOM(clk, rst_n, ahbReg_uLeafA_aphase, ahbReg_uLeafA_next_sel)
assign ahbReg_uLeafA_ready = ahbReg_uLeafA_sel & ~ahbReg_uLeafA_aphase & ahbReg_uLeafA.hreadyout;
`SCFF_DOM(clk, rst_n, ahbReg_uLeafA_sel, ahbReg_uLeafA_next_sel, ahbReg_uLeafA_ready)

assign ahbReg_uLeafA.hsel   = ahbReg_uLeafA_aphase;
assign ahbReg_uLeafA.htrans = ahbReg_uLeafA_aphase ? 2'b10 : 2'b00;
assign ahbReg_uLeafA.haddr  = haddr_q;
assign ahbReg_uLeafA.hwrite = hwrite_q;
assign ahbReg_uLeafA.hsize  = hsize_q;
assign ahbReg_uLeafA.hwdata = hwdata_q;
assign ahbReg_uLeafA.hready = ahbReg_uLeafA.hreadyout;

always_comb begin
    ahbReg_uSubSys_next_sel = 1'b0;
    ahbReg_uLeafB_next_sel = 1'b0;
    ahbReg_uLeafA_next_sel = 1'b0;
    ahb_accept = 1'b0;
    if (ahbReg.hsel & ahbReg.htrans[1] & ahbReg.hready) begin
        ahb_accept = 1'b1;
        if (ahb_addr >= ahbAddrSt'(32'h3000)) begin
            // unmapped, selects no child
        end else if (ahb_addr >= ahbAddrSt'(32'h2000)) begin
            ahbReg_uSubSys_next_sel = '1;
        end else if (ahb_addr >= ahbAddrSt'(32'h1000)) begin
            ahbReg_uLeafB_next_sel = '1;
        end else begin
            ahbReg_uLeafA_next_sel = '1;
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
    if (ahbReg_uSubSys_sel) begin
        ahbReg_next_hready = ahbReg_uSubSys_ready;
        ahbReg_next_hrdata = ahbReg_uSubSys.hrdata;
        ahbReg_next_hresp  = ahbReg_uSubSys.hresp;
    end else if (ahbReg_uLeafB_sel) begin
        ahbReg_next_hready = ahbReg_uLeafB_ready;
        ahbReg_next_hrdata = ahbReg_uLeafB.hrdata;
        ahbReg_next_hresp  = ahbReg_uLeafB.hresp;
    end else if (ahbReg_uLeafA_sel) begin
        ahbReg_next_hready = ahbReg_uLeafA_ready;
        ahbReg_next_hrdata = ahbReg_uLeafA.hrdata;
        ahbReg_next_hresp  = ahbReg_uLeafA.hresp;
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

endmodule: ahbRouter
// GENERATED_CODE_END
