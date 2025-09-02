//

// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: axi4sDemo
module axi4sDemo
// Generated Import package statement(s)
import axi4sDemo_tb_package::*;
(
    axi4_stream_if.dst axis4_t1,
    axi4_stream_if.src axis4_t2,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances

// GENERATED_CODE_END

    localparam int SRC_DATA_WIDTH = 256;
    localparam int DST_DATA_WIDTH = 64;

    // Parameter sanity checks (simulation-time)
    localparam int SRC_BYTES = SRC_DATA_WIDTH / 8;
    localparam int DST_BYTES = DST_DATA_WIDTH / 8;
    localparam int RATIO     = (DST_DATA_WIDTH == 0) ? 1 : (SRC_DATA_WIDTH / DST_DATA_WIDTH);

    // Basic guards for ratio-based downsizing
    initial begin
        if (SRC_DATA_WIDTH != 256 || DST_DATA_WIDTH != 64) begin
            $warning("axi4_stream_downsizer: Port widths are fixed (256->64). Parameters set to %0d->%0d; ensure they match the ports.",
                     SRC_DATA_WIDTH, DST_DATA_WIDTH);
        end
        if (SRC_DATA_WIDTH % DST_DATA_WIDTH != 0) begin
            $error("axi4_stream_downsizer: SRC_DATA_WIDTH (%0d) must be an integer multiple of DST_DATA_WIDTH (%0d).",
                   SRC_DATA_WIDTH, DST_DATA_WIDTH);
        end
    end

    // Buffer registers for one input beat
    logic                        have_word;
    logic [SRC_DATA_WIDTH-1:0]   data_reg;
    logic [SRC_BYTES-1:0]        keep_reg;
    logic [SRC_BYTES-1:0]        strb_reg;
    logic                        last_reg;
    logic [3:0]                  id_reg;
    logic [3:0]                  dest_reg;
    logic [15:0]                 user_reg;

    // Chunk tracking
    logic [$clog2((RATIO>0)?RATIO:1):0] chunk_idx;     // current chunk index
    logic [$clog2((RATIO>0)?RATIO:1):0] chunks_total;  // number of chunks to emit for this input beat (1..RATIO)

    // Helper: count contiguous valid bytes from LSB in TKEEP for last beat
    function automatic int unsigned count_valid_bytes(input logic [SRC_BYTES-1:0] k, input logic last);
        int unsigned c;
        int i;
        if (!last) return SRC_BYTES;
        c = 0;
        for (i = 0; i < SRC_BYTES; i++) begin
            if (k[i]) c++; else break;
        end
        // Fallback in case of malformed last-beat keep (should not happen per AXI4-Stream)
        if (c == 0) c = SRC_BYTES;
        return c;
    endfunction

    // Ready to accept a new input beat only when not currently holding one
    assign axis4_t1.tready = !have_word;

    // Variable part-select bases (bit and byte)
    wire int unsigned bit_base  = int'(chunk_idx) * DST_DATA_WIDTH;
    wire int unsigned byte_base = int'(chunk_idx) * DST_BYTES;

    // Output muxing; drive zeros when not valid
    wire                        out_valid = have_word;
    wire [DST_DATA_WIDTH-1:0]   out_data  = data_reg[bit_base +: DST_DATA_WIDTH];
    wire [DST_BYTES-1:0]        out_keep  = keep_reg[byte_base +: DST_BYTES];
    wire [DST_BYTES-1:0]        out_strb  = strb_reg[byte_base +: DST_BYTES];
    wire                        out_last  = last_reg && (chunk_idx == (chunks_total - 1));

    assign axis4_t2.tvalid = out_valid;
    assign axis4_t2.tdata  = out_valid ? out_data : '0;
    assign axis4_t2.tkeep  = out_valid ? out_keep : '0;
    assign axis4_t2.tstrb  = out_valid ? out_strb : '0;
    assign axis4_t2.tlast  = out_valid ? out_last : 1'b0;
    assign axis4_t2.tid    = out_valid ? id_reg   : '0;
    assign axis4_t2.tdest  = out_valid ? dest_reg : '0;
    // Map lower 4 bits of input TUSER to output (width change 16 -> 4)
    assign axis4_t2.tuser  = out_valid ? user_reg[3:0] : '0;

    // Handshake detection
    wire out_fire = axis4_t2.tvalid && axis4_t2.tready;
    wire in_fire  = axis4_t1.tvalid && axis4_t1.tready;

    // Sequential logic
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            have_word    <= 1'b0;
            data_reg     <= '0;
            keep_reg     <= '0;
            strb_reg     <= '0;
            last_reg     <= 1'b0;
            id_reg       <= '0;
            dest_reg     <= '0;
            user_reg     <= '0;
            chunk_idx    <= '0;
            chunks_total <= '0;
        end else begin
            // Accept a new input beat when ready
            if (in_fire) begin
                int unsigned vb;
                int unsigned ct;

                data_reg  <= axis4_t1.tdata;
                keep_reg  <= axis4_t1.tkeep;
                strb_reg  <= axis4_t1.tstrb;
                last_reg  <= axis4_t1.tlast;
                id_reg    <= axis4_t1.tid;
                dest_reg  <= axis4_t1.tdest;
                user_reg  <= axis4_t1.tuser;

                // Determine how many output chunks to send for this beat
                vb = count_valid_bytes(axis4_t1.tkeep, axis4_t1.tlast);
                ct = (vb + DST_BYTES - 1) / DST_BYTES; // ceil division
                if (ct == 0) ct = 1; // safety
                chunks_total <= ct[$bits(chunks_total)-1:0];

                chunk_idx  <= '0;
                have_word  <= 1'b1;
            end else if (out_fire && have_word) begin
                // Advance to next chunk or release the word
                if (chunk_idx + 1 < chunks_total) begin
                    chunk_idx <= chunk_idx + 1;
                end else begin
                    // Finished all chunks for this word
                    have_word  <= 1'b0;
                    chunk_idx  <= '0;
                    chunks_total <= '0;
                end
            end
        end
    end

endmodule: axi4sDemo