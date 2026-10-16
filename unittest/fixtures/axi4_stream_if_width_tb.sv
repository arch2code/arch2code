// Self-checking testbench for interfaces/axi4_stream/axi4_stream_if.sv, built
// standalone by unittest/test_axi4_stream_if_width_sim.py with Verilator
// `--binary --timing`. tkeep and tstrb must carry one bit per tdata byte.
// For logic [3:0][7:0], $size and $bits differ on every simulator; the
// module-local struct reproduces a VCS W-2024.09-SP2 $size bug only VCS fails.
// Prints TB_PASS on success; any mismatch ends in $fatal.

// A payload typedef'd inside a parameterized module: a packed struct holding
// a packed array of packed structs.
module axi4_stream_if_width_rgb #(parameter int BPP = 8, parameter int PPC = 4) (
    output int tdata_bits,
    output int tkeep_bits,
    output int tstrb_bits
);
    typedef logic [BPP-1:0] pixel_t;
    typedef struct packed { pixel_t b; pixel_t g; pixel_t r; } rgb_pixel_t;
    typedef struct packed { rgb_pixel_t [PPC-1:0] pixels; } rgb_pixels_per_clock_t;

    axi4_stream_if #(.tdata_t(rgb_pixels_per_clock_t)) s();

    assign tdata_bits = $bits(rgb_pixels_per_clock_t);
    assign tkeep_bits = $bits(s.tkeep);
    assign tstrb_bits = $bits(s.tstrb);
endmodule: axi4_stream_if_width_rgb

module axi4_stream_if_width_tb;

typedef logic [3:0][7:0] bytes_t;
axi4_stream_if #(.tdata_t(bytes_t)) s_bytes();

int rgb_tdata_bits, rgb_tkeep_bits, rgb_tstrb_bits;
axi4_stream_if_width_rgb #(.BPP(8), .PPC(4)) u_rgb (
    .tdata_bits (rgb_tdata_bits), .tkeep_bits (rgb_tkeep_bits),
    .tstrb_bits (rgb_tstrb_bits));

int unsigned errors = 0;

task automatic check(input string label, input int tdata_bits, input int expected,
                     input int tkeep_bits, input int tstrb_bits);
    logic ok;
    begin
        ok = tdata_bits / 8 == expected && tkeep_bits == expected && tstrb_bits == expected;
        if (!ok) begin
            $display("    %s: tdata=%0d bits, tkeep=%0d tstrb=%0d, expected %0d",
                     label, tdata_bits, tkeep_bits, tstrb_bits, expected);
            errors++;
        end
        $display("  %-40s tkeep=%0d tstrb=%0d  %s", label, tkeep_bits, tstrb_bits,
                 ok ? "PASS" : "FAIL");
    end
endtask

initial begin
    #1;
    check("tdata_t logic [3:0][7:0]", $bits(bytes_t), 4,
          $bits(s_bytes.tkeep), $bits(s_bytes.tstrb));
    check("tdata_t module-local rgb pixels", rgb_tdata_bits, 12,
          rgb_tkeep_bits, rgb_tstrb_bits);

    $display("=== %s (%0d errors) ===", (errors == 0) ? "PASS" : "FAIL", errors);
    if (errors != 0)
        $fatal(1, "axi4_stream_if_width_tb: %0d errors", errors);
    $display("TB_PASS");
    $finish;
end

endmodule: axi4_stream_if_width_tb
