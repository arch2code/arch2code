// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: blockA
module blockA
// Generated Import package statement(s)
import mixedInclude_package::*;
import mixedBlockC_package::*;
import mixed_package::*;
(
    req_ack_if.src aStuffIf,
    rdy_vld_if.src cStuffIf,
    notify_ack_if.src startDone,
    rdy_vld_if.src dupIf,
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    status_if #(.data_t(aRegSt)) roA();
    memory_if #(.data_t(aRegSt), .addr_t(bSizeSt)) blockATableLocal();
    memory_if #(.data_t(test37BitRegSt), .addr_t(bSizeSt)) blockATable37Bit();

// Instances
blockARegs uBlockARegs (
    .apbReg (apbReg),
    .roA (roA),
    .blockATableLocal (blockATableLocal),
    .blockATable37Bit (blockATable37Bit),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

// Memory storage for blockATableLocal
aRegSt blockATableLocal_mem [0:BSIZE-1];

// Initialize with pattern i * 0x22
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (int i = 0; i < BSIZE; i++) begin
            blockATableLocal_mem[i] <= aRegSt'(i * 7'h22);
        end
    end
end

// Memory responder for blockATableLocal
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        blockATableLocal.read_data <= '0;
    end else if (blockATableLocal.enable) begin
        if (blockATableLocal.wr_en) begin
            blockATableLocal_mem[blockATableLocal.addr] <= blockATableLocal.write_data;
        end
        blockATableLocal.read_data <= blockATableLocal_mem[blockATableLocal.addr];
    end
end

// Memory storage for blockATable37Bit
test37BitRegSt blockATable37Bit_mem [0:BSIZE-1];

// Initialize memory with pattern (i << 32) | i
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (int i = 0; i < BSIZE; i++) begin
            blockATable37Bit_mem[i] <= test37BitRegSt'({i[4:0], i[31:0]});
        end
    end
end

// Memory responder for blockATable37Bit
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        blockATable37Bit.read_data <= '0;
    end else if (blockATable37Bit.enable) begin
        if (blockATable37Bit.wr_en) begin
            blockATable37Bit_mem[blockATable37Bit.addr] <= blockATable37Bit.write_data;
        end
        blockATable37Bit.read_data <= blockATable37Bit_mem[blockATable37Bit.addr];
    end
end

endmodule: blockA