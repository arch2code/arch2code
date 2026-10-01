// Dual-port memory. Port A and port B have independent clocks (clkA / clkB).
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
    input clkA,
    input clkB
);

    typedef logic [$size(mem_portA.addr)-1:0] _addrA_t;
    typedef logic [$size(mem_portB.addr)-1:0] _addrB_t;
    typedef logic [$size(data_t)-1:0] _data_t;

    // Port A

    _addrA_t addrA;
    _data_t write_dataA, read_dataA;

    assign addrA = _addrA_t'(mem_portA.addr);
    assign write_dataA = _data_t'(mem_portA.write_data);

    // single cycle flop'd output on reads
    generate if (PORTA_READ_ONLY) begin : g_portA_ro
        // No write path at all, rather than a write guarded by a constant, so
        // the inferred RAM has one write port however hard the tool squints.
        always @(posedge clkA) begin
            if (mem_portA.enable) begin
                read_dataA <= mem[addrA];
            end
        end
    end else begin : g_portA_rw
        always @(posedge clkA) begin
            if (mem_portA.enable && mem_portA.wr_en) begin
                mem[addrA] <= write_dataA;
            end else if (mem_portA.enable) begin
                read_dataA <= mem[addrA];
            end
        end
    end endgenerate

    assign mem_portA.read_data = data_t'(read_dataA);

    // Port B

    _addrB_t addrB;
    _data_t write_dataB, read_dataB;

    assign addrB = _addrB_t'(mem_portB.addr);
    assign write_dataB = _data_t'(mem_portB.write_data);

    // single cycle flop'd output on reads (port B runs on its own clock clkB)
    generate if (PORTB_WRITE_ONLY) begin : g_portB_wo
        always @(posedge clkB) begin
            if (mem_portB.enable && mem_portB.wr_en) begin
                mem[addrB] <= write_dataB;
            end
        end
        assign read_dataB = '0;
    end else begin : g_portB_rw
        always @(posedge clkB) begin
            if (mem_portB.enable && mem_portB.wr_en) begin
                mem[addrB] <= write_dataB;
            end else if (mem_portB.enable) begin
                read_dataB <= mem[addrB];
            end
        end
    end endgenerate

    assign mem_portB.read_data = data_t'(read_dataB);

endmodule : memory_dp_ext
