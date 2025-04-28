module memory_dp #(
    parameter DEPTH  = 2 ,
    parameter type data_t = logic [1:0])
(
    memory_if.dst mem_portA,
    memory_if.dst mem_portB,
    input clk
);

    typedef logic [$size(mem_portA.addr)-1:0] _addrA_t;
    typedef logic [$size(mem_portB.addr)-1:0] _addrB_t;
    typedef logic [$size(data_t)-1:0] _data_t;

    _data_t mem [DEPTH-1:0]; /* verilator lint_off WIDTHTRUNC */

    // Port A

    _addrA_t addrA;
    _data_t write_dataA, read_dataA;

    assign addrA = _addrA_t'(mem_portA.addr);
    assign write_dataA = _data_t'(mem_portA.write_data);

    // single cycle flop'd output on reads
    always @(posedge clk) begin
        if (mem_portA.enable && mem_portA.wr_en) begin
            mem[addrA] <= write_dataA;
        end else if (mem_portA.enable) begin
            read_dataA <= mem[addrA];
        end
    end

    assign mem_portA.read_data = data_t'(read_dataA);

    // Port B

    _addrB_t addrB;
    _data_t write_dataB, read_dataB;

    assign addrB = _addrB_t'(mem_portB.addr);
    assign write_dataB = _data_t'(mem_portB.write_data);

    // single cycle flop'd output on reads
    always @(posedge clk) begin
        if (mem_portB.enable && mem_portB.wr_en) begin
            mem[addrB] <= write_dataB;
        end else if (mem_portB.enable) begin
            read_dataB <= mem[addrB];
        end
    end

    assign mem_portB.read_data = data_t'(read_dataB);

endmodule : memory_dp
