//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subSys
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: subSys
module subSys
// Generated Import package statement(s)
import ahbDecode_package::*;
(
    ahb_if.dst ahbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    ahb_if #(.addr_t(ahbAddrSt), .data_t(ahbDataSt)) ahbReg_uLeafC();

// Instances
subRouter uSubRouter (
    .ahbReg (ahbReg),
    .ahbReg_uLeafC (ahbReg_uLeafC),
    .clk (clk),
    .rst_n (rst_n)
);

leafB uLeafC (
    .ahbReg (ahbReg_uLeafC),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: subSys
