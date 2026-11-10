//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=leafB
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: leafB
module leafB
// Generated Import package statement(s)
import ahbDecode_package::*;
(
    ahb_if.dst ahbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    status_if #(.data_t(cfgRegSt)) cfgB();

// Instances
leafBRegs uleafBRegs (
    .ahbReg (ahbReg),
    .cfgB (cfgB),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: leafB
