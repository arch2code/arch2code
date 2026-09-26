// GENERATED_CODE_PARAM --block=blockD
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: blockD
module blockD
// Generated Import package statement(s)
import mixedInclude_package::*;
import mixedBlockC_package::*;
import mixed_package::*;
(
    rdy_vld_if.src cStuffIf,
    rdy_vld_if.src dee0,
    rdy_vld_if.src dee1,
    rdy_vld_if.src outD,
    rdy_vld_if.dst inD,
    req_ack_if.dst btod,
    status_if.dst rwD,
    status_if.src roBsize,
    memory_if.dst blockBTableExt,
    memory_if.dst blockBTable37Bit,
    memory_if.src blockBTable1,
    memory_if.src blockBTableSP,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

// Memory storage for blockBTable37Bit (external listener)
test37BitRegSt blockBTable37Bit_mem [0:BSIZE-1];

// Initialize memory with pattern (i << 32) | i
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (int i = 0; i < BSIZE; i++) begin
            blockBTable37Bit_mem[i] <= test37BitRegSt'({i[4:0], i[31:0]});
        end
    end else if (blockBTable37Bit.enable && blockBTable37Bit.wr_en) begin
        blockBTable37Bit_mem[blockBTable37Bit.addr] <= blockBTable37Bit.write_data;
    end
end

// Memory storage for blockBTableExt (external listener)
seeSt blockBTableExt_mem [0:BSIZE-1];

// Initialize to zeros
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (int i = 0; i < BSIZE; i++) begin
            blockBTableExt_mem[i] <= seeSt'(0);
        end
    end else if (blockBTableExt.enable && blockBTableExt.wr_en) begin
        blockBTableExt_mem[blockBTableExt.addr] <= blockBTableExt.write_data;
    end
end

endmodule: blockD
