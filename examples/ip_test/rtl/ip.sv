//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: ip
module ip
// Generated Import package statement(s)
import ip_top_package::*;
import ip_package::*;
#(
    parameter IP_DATA_WIDTH,
    parameter IP_MEM_DEPTH
)
(
    rdy_vld_if.dst ipDataIf,
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    status_if #(.data_t(ipCfgSt)) ipCfg();

// Instances
ipRegs uIpRegs (
    .apbReg (apbReg),
    .ipCfg (ipCfg),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: ip
