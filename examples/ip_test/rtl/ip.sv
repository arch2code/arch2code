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
    push_ack_if.dst ipDataIf,
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    status_if #(.data_t(ipCfgSt)) ipCfg();
    status_if #(.data_t(ipDataSt)) ipLastData();

// Instances
ipRegs uIpRegs (
    .apbReg (apbReg),
    .ipCfg (ipCfg),
    .ipLastData (ipLastData),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

    // Capture incoming push data into ipLastData (status_if to ipRegs).
    // Ack on the same cycle a push is observed.
    `DFF_INST(ipDataSt, lastData)

    always_comb begin
        n_lastData = lastData;
        ipDataIf.ack = 1'b0;
        if (ipDataIf.push) begin
            n_lastData = ipDataIf.data;
            ipDataIf.ack = 1'b1;
        end
    end

    assign ipLastData.data = lastData;

endmodule: ip
