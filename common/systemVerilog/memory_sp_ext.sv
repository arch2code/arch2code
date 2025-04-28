module memory_sp_ext #(
    parameter DEPTH  = 2 ,
    parameter type data_t = logic [1:0])
(
    memory_if.dst mem_port,
    output logic [$size(data_t)-1:0] mem [DEPTH-1:0],
    input clk
);

    typedef logic [$size(mem_port.addr)-1:0] _addr_t;
    typedef logic [$size(data_t)-1:0] _data_t;

    _addr_t addr;
    _data_t write_data, read_data;

    assign addr = _addr_t'(mem_port.addr);
    assign write_data = _data_t'(mem_port.write_data);

    // single cycle flop'd output on reads
    always @(posedge clk) begin
        if (mem_port.enable && mem_port.wr_en) begin
            mem[addr] <= write_data;
        end else if (mem_port.enable) begin
            read_data <= mem[addr];
        end
    end

    assign mem_port.read_data = data_t'(read_data);

endmodule : memory_sp_ext
