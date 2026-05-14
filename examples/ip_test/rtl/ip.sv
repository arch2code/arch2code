//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: ip
module ip
// Generated Import package statement(s)
import ip_top_package::*;
import ip_package::*;
#(
    parameter IP_DATA_WIDTH,
    parameter IP_MEM_DEPTH,
    parameter IP_NONCONST_DEPTH
)
(
    push_ack_if.dst ipDataIf,
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    status_if #(.data_t(ipCfgSt)) ipCfg();
    status_if #(.data_t(ipDataSt)) ipLastData();

    // Memory Interfaces
    memory_if #(.data_t(ipMemSt), .addr_t(ipMemAddrSt)) ipMem();
    memory_if #(.data_t(ipMemSt), .addr_t(ipMemAddrSt)) ipMem_reg();
    memory_if #(.data_t(ipFixedSt), .addr_t(ipFixedAddrSt)) ipFixedMem();
    memory_if #(.data_t(ipFixedSt), .addr_t(ipFixedAddrSt)) ipFixedMem_reg();
    memory_if #(.data_t(ipFixedSt), .addr_t(ipFixedAddrSt)) ipNonConstMem();
    memory_if #(.data_t(ipFixedSt), .addr_t(ipFixedAddrSt)) ipNonConstMem_reg();

// Instances
ipRegs uIpRegs (
    .apbReg (apbReg),
    .ipMem (ipMem_reg),
    .ipFixedMem (ipFixedMem_reg),
    .ipNonConstMem (ipNonConstMem_reg),
    .ipCfg (ipCfg),
    .ipLastData (ipLastData),
    .clk (clk),
    .rst_n (rst_n)
);

// Memory Instances
memory_dp #(.DEPTH(IP_MEM_DEPTH), .data_t(ipMemSt)) uIpMem (
    .mem_portA (ipMem),
    .mem_portB (ipMem_reg),
    .clk (clk)
);

memory_dp #(.DEPTH(IP_MEM_DEPTH), .data_t(ipFixedSt)) uIpFixedMem (
    .mem_portA (ipFixedMem),
    .mem_portB (ipFixedMem_reg),
    .clk (clk)
);

memory_dp #(.DEPTH(IP_NONCONST_DEPTH), .data_t(ipFixedSt)) uIpNonConstMem (
    .mem_portA (ipNonConstMem),
    .mem_portB (ipNonConstMem_reg),
    .clk (clk)
);

// GENERATED_CODE_END

    // Capture incoming push data into ipLastData (status_if to ipRegs).
    // Ack on the same cycle a push is observed.
    `DFF_INST(ipDataSt, lastData)

    always_comb begin
        n_lastData = lastData;
        ipDataIf.ack = 1'b0;
        if (ipDataIf.push) begin
            // TODO(SV parameterization): remove this field-wise widening once
            // parameterizable package types become module-local types driven by
            // this instance's IP_DATA_WIDTH parameter. Today ipDataSt/ipDataT
            // come from ip_package at the max/default width, so variant0's
            // narrower push_ack payload must be widened without moving marker.
            n_lastData = '0;
            n_lastData.marker = ipDataIf.data.marker;
            n_lastData.data = ipDataT'(ipDataIf.data.data);
            ipDataIf.ack = 1'b1;
        end
    end

    assign ipLastData.data = lastData;

endmodule: ip
