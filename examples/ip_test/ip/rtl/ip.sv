//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: ip
module ip
// Generated Import package statement(s)
import ip_package::*;
#(
    parameter IP_DATA_WIDTH,
    parameter IP_MEM_DEPTH,
    parameter IP_NONCONST_DEPTH
)
(
    push_ack_if.dst ipDataIf,
    apb_if.dst regs,
    input clk, rst_n
);

    // Module-local parameterizable type/struct declarations
    localparam IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2; //Derived width, 2x data (maxValue auto-derived); eval-derived, lives in constants: since no block param consumes it
    localparam IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2; //Second-level derived width, 4x data
    localparam IP_MEM_DEPTH_X2 = IP_MEM_DEPTH * 2; //Derived memory depth, 2x depth
    localparam IP_MEM_DEPTH_X4 = IP_MEM_DEPTH_X2 * 2; //Second-level derived memory depth, 4x depth
    typedef logic[IP_DATA_WIDTH-1:0] ipDataT; //IP data word, parameterizable
    typedef logic[$clog2(IP_MEM_DEPTH)-1:0] ipMemAddrT; //Index into ipMem (0 .. IP_MEM_DEPTH-1)
    typedef logic[IP_DATA_WIDTH_X4-1:0] ipDerivedWidthT; //Type sized by a second-level eval-derived localparam
    typedef logic[$clog2(IP_MEM_DEPTH_X4)-1:0] ipDerivedMemAddrT; //Index into second-level derived-depth memory
    typedef logic signed[IP_MEM_DEPTH-1:0] ipSignedParamT; //Signed parameterizable value, width tracks IP_MEM_DEPTH
    typedef struct packed {
        enableT marker; //Marker bit expected after the data payload
        ipDataT data; //Data word
    } ipDataSt;
    typedef struct packed {
        enableT enable; //Enable bit
        ipModeT mode; //Operating mode
        ipDataT threshold; //Threshold value
    } ipCfgSt;
    typedef struct packed {
        ipDataT data; //Data word
    } ipMemSt;
    typedef struct packed {
        ipMemAddrT address; //Memory address
    } ipMemAddrSt;
    typedef struct packed {
        ipDataT [IP_MEM_DEPTH-1:0] samples; //Burst of parameterizable samples
    } ipBurstSt;
    typedef struct packed {
        ipDerivedMemAddrT address; //Second-level derived-depth memory address
    } ipDerivedMemAddrSt;
    typedef struct packed {
        ipCfgSt cfg; //Single nested parameterizable config sub-struct
        ipDataSt [2-1:0] payloads; //Parameterizable nested sub-struct array
    } ipParamNestedSt;
    typedef struct packed {
        ipSignedParamT offset; //Signed parameterizable field
        ipMemAddrT index; //Unsigned parameterizable field below it
    } ipSignedParamSt;

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
    memory_if #(.data_t(ipMemSt), .addr_t(ipDerivedMemAddrSt)) ipDerivedDepthMem();
    memory_if #(.data_t(ipMemSt), .addr_t(ipDerivedMemAddrSt)) ipDerivedDepthMem_unused();

// Instances
ip_ipRegs #(.IP_DATA_WIDTH(IP_DATA_WIDTH), .IP_MEM_DEPTH(IP_MEM_DEPTH), .IP_NONCONST_DEPTH(IP_NONCONST_DEPTH)) uIpRegs (
    .ipReg (regs),
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

memory_dp #(.DEPTH(IP_MEM_DEPTH_X4), .data_t(ipMemSt)) uIpDerivedDepthMem (
    .mem_portA (ipDerivedDepthMem),
    .mem_portB (ipDerivedDepthMem_unused),
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
            n_lastData = ipDataIf.data;
            ipDataIf.ack = 1'b1;
        end
    end

    assign ipLastData.data = lastData;

endmodule: ip
