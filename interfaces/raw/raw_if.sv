/*
 * Raw Interface (Blocking) — LAST RESORT
 *
 * Prefer rdy_vld / push_ack / axi4_stream for new interconnect. Use raw only at
 * design boundaries when adapting to legacy/external IP with a free-running
 * data bus and no ready/valid/ack wires. Do not use for new internal links
 * between arch2code blocks. See ARCH2CODE_AI_RULES.md (§ raw).
 *
 *                  ______________________
 *  src.data  _____/         DATA         \__
 *
 * RTL: data only (no handshake). SystemC: blocking write/read rendezvous.
 */

interface raw_if #(
        parameter type data_t = logic
    );

    data_t data;

    // Source
    modport src (output data);

    // Destination
    modport dst (input data);

endinterface : raw_if
