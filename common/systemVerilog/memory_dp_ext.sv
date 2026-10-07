// Dual-port memory with a single clock for both ports, exposing the array as
// an output. Modes as memory_dp.
module memory_dp_ext #(
    parameter DEPTH  = 2 ,
    parameter type data_t = logic [1:0],
    // 1: port A reads only and ignores writes.
    parameter bit PORTA_READ_ONLY = 1'b0,
    // 1: port B writes only; reads return zero.
    parameter bit PORTB_WRITE_ONLY = 1'b0)
(
    memory_if.dst mem_portA,
    memory_if.dst mem_portB,
    output logic [$size(data_t)-1:0] mem [DEPTH-1:0],
    input clk
);

    typedef logic [$size(mem_portA.addr)-1:0] _addrA_t;
    typedef logic [$size(mem_portB.addr)-1:0] _addrB_t;
    typedef logic [$size(data_t)-1:0] _data_t;

    _addrA_t addrA;
    _addrB_t addrB;
    _data_t write_dataA, read_dataA;
    _data_t write_dataB, read_dataB;

    assign addrA = _addrA_t'(mem_portA.addr);
    assign write_dataA = _data_t'(mem_portA.write_data);
    assign addrB = _addrB_t'(mem_portB.addr);
    assign write_dataB = _data_t'(mem_portB.write_data);

    // All reads and writes in one always block per mode, so each storage bit
    // has a single driver. Reads are single cycle flop'd and return the old
    // contents on a same-address read and write. A read-only port has no write
    // statement at all, so the inferred RAM has only the write ports the mode
    // needs.
    generate
        if (PORTA_READ_ONLY && PORTB_WRITE_ONLY) begin : g_1w1r
            always @(posedge clk) begin
                if (mem_portB.enable && mem_portB.wr_en) begin
                    mem[addrB] <= write_dataB;
                end
                if (mem_portA.enable) begin
                    read_dataA <= mem[addrA];
                end
            end
            assign read_dataB = '0;
        end else if (PORTA_READ_ONLY) begin : g_1rw1r
            always @(posedge clk) begin
                if (mem_portB.enable && mem_portB.wr_en) begin
                    mem[addrB] <= write_dataB;
                end else if (mem_portB.enable) begin
                    read_dataB <= mem[addrB];
                end
                if (mem_portA.enable) begin
                    read_dataA <= mem[addrA];
                end
            end
        end else if (!PORTB_WRITE_ONLY) begin : g_2rw
            always @(posedge clk) begin
                if (mem_portA.enable && mem_portA.wr_en) begin
                    mem[addrA] <= write_dataA;
                end else if (mem_portA.enable) begin
                    read_dataA <= mem[addrA];
                end
                // After port A, so port B wins a same-address double write.
                if (mem_portB.enable && mem_portB.wr_en) begin
                    mem[addrB] <= write_dataB;
                end else if (mem_portB.enable) begin
                    read_dataB <= mem[addrB];
                end
            end
        end else begin : g_rw_wo
            always @(posedge clk) begin
                if (mem_portA.enable && mem_portA.wr_en) begin
                    mem[addrA] <= write_dataA;
                end else if (mem_portA.enable) begin
                    read_dataA <= mem[addrA];
                end
                // After port A, so port B wins a same-address double write.
                if (mem_portB.enable && mem_portB.wr_en) begin
                    mem[addrB] <= write_dataB;
                end
            end
            assign read_dataB = '0;
        end
    endgenerate

    assign mem_portA.read_data = data_t'(read_dataA);
    assign mem_portB.read_data = data_t'(read_dataB);

endmodule : memory_dp_ext
