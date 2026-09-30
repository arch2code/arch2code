`ifndef _MIXED_HDL_SV_WRAPPER_SV_GUARD_
`define _MIXED_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module mixed_hdl_sv_wrapper
    // Generated Import package statement(s)
    import mixedBlockC_package::*;
    import mixed_package::*;
(
    // apb_if.dst
    input bit [31:0] cpu_main_paddr,
    input bit cpu_main_psel,
    input bit cpu_main_penable,
    input bit cpu_main_pwrite,
    input bit [31:0] cpu_main_pwdata,
    output bit cpu_main_pready,
    output bit [31:0] cpu_main_prdata,
    output bit cpu_main_pslverr,

    input clk,
    input rst_n
);
    // apb_if.dst
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) cpu_main();

    assign #0 cpu_main.paddr = cpu_main_paddr;
    assign #0 cpu_main.psel = cpu_main_psel;
    assign #0 cpu_main.penable = cpu_main_penable;
    assign #0 cpu_main.pwrite = cpu_main_pwrite;
    assign #0 cpu_main.pwdata = cpu_main_pwdata;
    assign #0 cpu_main_pready = cpu_main.pready;
    assign #0 cpu_main_prdata = cpu_main.prdata;
    assign #0 cpu_main_pslverr = cpu_main.pslverr;

    mixed dut (
        .cpu_main(cpu_main), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : mixed_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _MIXED_HDL_SV_WRAPPER_SV_GUARD_
