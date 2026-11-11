// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: blockF
module blockF
// Generated Import package statement(s)
import mixed_package::*;
import mixedBlockC_package::*;
#(
    parameter int unsigned bob = 32'h0000_0010,
    parameter int unsigned fred = 32'h0000_0000
)
(
    rdy_vld_if.src cStuffIf,
    rdy_vld_if.dst dStuffIf,
    rdy_vld_if.dst dSin,
    rdy_vld_if.src dSout,
    status_if.dst rwD,
    status_if.dst rwArr [REGARR_N],
    external_reg_if.dst extFArr,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

    // Memory Interfaces
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) test();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) test_unused();

// Instances
// Memory Instances
memory_dp #(.DEPTH(bob), .data_t(seeSt), .PORTA_READ_ONLY(1'b0), .PORTB_WRITE_ONLY(1'b0)) uTest (
    .mem_portA (test),
    .mem_portB (test_unused),
    .clk (clk)
);

// GENERATED_CODE_END


// Encodes the stimulus of test_reg_cpu_arr: element gi holds 0 or RWARR_SEED + gi. Another test that writes rwArr fails here.
for (genvar gi = 0; gi < REGARR_N; gi++) begin : g_rwArrChk
    always_comb begin
        `qAssertFatal(!rst_n || rwArr[gi].data.d == '0 || rwArr[gi].data.d == sevenBitT'(RWARR_SEED + gi), "blockF rwArr element misrouted")
    end
end

// extFArr reads back its last write + fred, so each instance answers with its own offset.
dRegSt extFWdata;
`DFFEN(extFWdata, extFArr.wdata, |extFArr.write)
assign extFArr.rdata.d = extFWdata.d + sevenBitT'(fred);

endmodule: blockF
