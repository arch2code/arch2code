`ifndef _IP_HDL_SV_WRAPPER_SVH_GUARD_
`define _IP_HDL_SV_WRAPPER_SVH_GUARD_

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=body

`include "hdlBoundary.svh"

module ip_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ip_package::*;
#(
    parameter IP_DATA_WIDTH,
    parameter IP_MEM_DEPTH,
    parameter IP_NONCONST_DEPTH,
    localparam IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2,
    localparam IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2,
    localparam IP_MEM_DEPTH_X2 = IP_MEM_DEPTH * 2,
    localparam IP_MEM_DEPTH_X4 = IP_MEM_DEPTH_X2 * 2
) (
    // push_ack_if.dst
    input bit ipDataIf_push,
    input bit [(IP_DATA_WIDTH + 1)-1:0] ipDataIf_data,
    output bit ipDataIf_ack,

    // apb_if.dst
    input bit [31:0] regs_paddr,
    input bit regs_psel,
    input bit regs_penable,
    input bit regs_pwrite,
    input bit [31:0] regs_pwdata,
    output bit regs_pready,
    output bit [31:0] regs_prdata,
    output bit regs_pslverr,

    input clk,
    input rst_n
);
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

    // push_ack_if.dst
    push_ack_if #(.data_t(ipDataSt)) ipDataIf();

    assign `A2C_HDL_BOUNDARY_DLY ipDataIf.push = ipDataIf_push;
    assign `A2C_HDL_BOUNDARY_DLY ipDataIf.data = ipDataIf_data;
    assign `A2C_HDL_BOUNDARY_DLY ipDataIf_ack = ipDataIf.ack;

    // apb_if.dst
    apb_if #(.addr_t(ipRegAddrSt), .data_t(ipRegDataSt)) regs();

    assign `A2C_HDL_BOUNDARY_DLY regs.paddr = regs_paddr;
    assign `A2C_HDL_BOUNDARY_DLY regs.psel = regs_psel;
    assign `A2C_HDL_BOUNDARY_DLY regs.penable = regs_penable;
    assign `A2C_HDL_BOUNDARY_DLY regs.pwrite = regs_pwrite;
    assign `A2C_HDL_BOUNDARY_DLY regs.pwdata = regs_pwdata;
    assign `A2C_HDL_BOUNDARY_DLY regs_pready = regs.pready;
    assign `A2C_HDL_BOUNDARY_DLY regs_prdata = regs.prdata;
    assign `A2C_HDL_BOUNDARY_DLY regs_pslverr = regs.pslverr;

    ip #(.IP_DATA_WIDTH(IP_DATA_WIDTH), .IP_MEM_DEPTH(IP_MEM_DEPTH), .IP_NONCONST_DEPTH(IP_NONCONST_DEPTH)) dut (
        .ipDataIf(ipDataIf), // push_ack_if.dst
        .regs(regs), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : ip_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _IP_HDL_SV_WRAPPER_SVH_GUARD_
