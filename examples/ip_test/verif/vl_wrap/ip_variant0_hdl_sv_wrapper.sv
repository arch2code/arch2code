`ifndef _IP_VARIANT0_HDL_SV_WRAPPER_SV_GUARD_
`define _IP_VARIANT0_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=ip --variant=variant0
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module ip_variant0_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ip_package::*;
(
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
    localparam IP_DATA_WIDTH = 8;
    localparam IP_MEM_DEPTH = 16;
    localparam IP_NONCONST_DEPTH = 24;
    typedef logic[IP_DATA_WIDTH-1:0] ipDataT; //IP data word, parameterizable
    typedef logic[$clog2(IP_MEM_DEPTH)-1:0] ipMemAddrT; //Index into ipMem (0 .. IP_MEM_DEPTH-1)
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

    // push_ack_if.dst
    push_ack_if #(.data_t(ipDataSt)) ipDataIf();

    assign #0 ipDataIf.push = ipDataIf_push;
    assign #0 ipDataIf.data = ipDataIf_data;
    assign #0 ipDataIf_ack = ipDataIf.ack;

    // apb_if.dst
    apb_if #(.addr_t(ipRegAddrSt), .data_t(ipRegDataSt)) regs();

    assign #0 regs.paddr = regs_paddr;
    assign #0 regs.psel = regs_psel;
    assign #0 regs.penable = regs_penable;
    assign #0 regs.pwrite = regs_pwrite;
    assign #0 regs.pwdata = regs_pwdata;
    assign #0 regs_pready = regs.pready;
    assign #0 regs_prdata = regs.prdata;
    assign #0 regs_pslverr = regs.pslverr;

    ip #(.IP_DATA_WIDTH(8), .IP_MEM_DEPTH(16), .IP_NONCONST_DEPTH(24)) dut (
        .ipDataIf(ipDataIf), // push_ack_if.dst
        .regs(regs), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : ip_variant0_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _IP_VARIANT0_HDL_SV_WRAPPER_SV_GUARD_
