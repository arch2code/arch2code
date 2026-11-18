//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ahbSoc
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: ahbSoc
module ahbSoc
// Generated Import package statement(s)
import ahbDecode_package::*;
(
    ahb_if.dst ahbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    ahb_if #(.addr_t(ahbAddrSt), .data_t(ahbDataSt)) ahbReg_uLeafA();
    ahb_if #(.addr_t(ahbAddrSt), .data_t(ahbDataSt)) ahbReg_uLeafB();
    ahb_if #(.addr_t(ahbAddrSt), .data_t(ahbDataSt)) ahbReg_uSubSys();

// Instances
ahbRouter uRouter (
    .ahbReg (ahbReg),
    .ahbReg_uLeafA (ahbReg_uLeafA),
    .ahbReg_uLeafB (ahbReg_uLeafB),
    .ahbReg_uSubSys (ahbReg_uSubSys),
    .clk (clk),
    .rst_n (rst_n)
);

leafA uLeafA (
    .ahbReg (ahbReg_uLeafA),
    .clk (clk),
    .rst_n (rst_n)
);

leafB uLeafB (
    .ahbReg (ahbReg_uLeafB),
    .clk (clk),
    .rst_n (rst_n)
);

subSys uSubSys (
    .ahbReg (ahbReg_uSubSys),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: ahbSoc
