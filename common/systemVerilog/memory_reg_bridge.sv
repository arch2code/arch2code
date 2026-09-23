// Bridges a register handler's bus-domain memory access to a memory on an
// independent clock and reset.
//
// Caller contract: hold req, wr, addr and wdata from the decode cycle until
// done, then drop req for at least one bus cycle before the next access. done
// is a one-cycle pulse; err and rdata are valid with it and hold until the
// next done. The contract holds across a reset on either side.
//
// Four-phase level handshake, one access outstanding: req_latch crosses to
// the memory side and ack crosses back. Two more levels prove the far side is
// out of reset. alive is set on the memory FSM's first MEM_IDLE after a reset
// and cleared when it is forced back to MEM_ARM; bus_alive is set once the bus
// side has seen alive low after a bus reset. A request completes with err at
// once while the bus side is reconnecting or alive reads low.
//
// An access reported with err after a memory reset may still have executed.
// The caller retries on err; register table writes are idempotent.
//
// Assumes each reset deasserts synchronously to its own clock, and that the
// memory clock runs (or the memory is held in reset) while the bus is out of
// reset; there is no timeout. Read latency is fixed at one memory cycle.

module memory_reg_bridge #(
    parameter type data_t = logic,
    parameter type addr_t = logic
) (
    input  bus_clk, input bus_rst_n,
    input  mem_clk, input mem_rst_n,
    // bus domain
    input  req, input wr, input addr_t addr, input data_t wdata,
    output logic done, output logic err, output data_t rdata,
    // memory domain
    memory_if.src mem_port
);

    // Not fsmDefs.svh: it assumes a single FSM on clk/rst_n.
    typedef enum logic [2:0] {
        MEM_ARM, MEM_IDLE, MEM_ACCESS, MEM_WAIT_RD, MEM_ACKED
    } mem_state_t;

    typedef enum logic [2:0] {
        BUS_ARM, BUS_CONNECT, BUS_IDLE, BUS_WAIT_ACK, BUS_WAIT_ACK_LOW, BUS_DRAIN
    } bus_state_t;

    // bus_alive_sync has four stages against req_sync's two, so req_sync_stable
    // is past its reset window whenever MEM_ARM first acts on it.
    `DFF_KEEP_INST_DOM(mem_clk, mem_rst_n, logic, req_sync_meta)
    `DFF_KEEP_INST_DOM(mem_clk, mem_rst_n, logic, req_sync_stable)
    `DFF_KEEP_INST_DOM(mem_clk, mem_rst_n, logic, bus_alive_sync_meta)
    `DFF_KEEP_INST_DOM(mem_clk, mem_rst_n, logic, bus_alive_sync_mid1)
    `DFF_KEEP_INST_DOM(mem_clk, mem_rst_n, logic, bus_alive_sync_mid2)
    `DFF_KEEP_INST_DOM(mem_clk, mem_rst_n, logic, bus_alive_sync_stable)
    `DFF_INST_DOM(mem_clk, mem_rst_n, logic, alive)
    `DFFR_INST_DOM(mem_clk, mem_rst_n, mem_state_t, mem_state, MEM_ARM)
    // Unreset, so a memory reset between ack and the bus sampling it cannot
    // zero the response.
    `DFFNR_INST_DOM(mem_clk, mem_rst_n, logic, err_hold)
    `DFFNR_INST_DOM(mem_clk, mem_rst_n, data_t, rdata_hold)
    `DFF_INST_DOM(mem_clk, mem_rst_n, logic, ack)

    // Reset to 1: the bus side only proceeds on a real 0 from these chains,
    // so a reset value can only lengthen a wait.
    `DFFR_KEEP_INST_DOM(bus_clk, bus_rst_n, logic, alive_sync_meta, 1'b1)
    `DFFR_KEEP_INST_DOM(bus_clk, bus_rst_n, logic, alive_sync_stable, 1'b1)
    `DFFR_KEEP_INST_DOM(bus_clk, bus_rst_n, logic, ack_sync_meta, 1'b1)
    `DFFR_KEEP_INST_DOM(bus_clk, bus_rst_n, logic, ack_sync_stable, 1'b1)
    `DFF_INST_DOM(bus_clk, bus_rst_n, logic, req_taken)
    `DFF_INST_DOM(bus_clk, bus_rst_n, logic, req_latch)
    `DFF_INST_DOM(bus_clk, bus_rst_n, logic, bus_alive)
    `DFFR_INST_DOM(bus_clk, bus_rst_n, bus_state_t, bus_state, BUS_ARM)

    logic start_access;
    // Unreset, so a bus reset cannot corrupt a write the memory side is still
    // performing.
    `DFFNR_INST_DOM(bus_clk, bus_rst_n, logic, latched_wr)
    `DFFNR_INST_DOM(bus_clk, bus_rst_n, addr_t, latched_addr)
    `DFFNR_INST_DOM(bus_clk, bus_rst_n, data_t, latched_wdata)
    `DFFEN_INST_DOM(bus_clk, bus_rst_n, logic, bus_err_q, done)
    `DFFEN_INST_DOM(bus_clk, bus_rst_n, data_t, bus_rdata_q, done)

    logic err_new;
    data_t rdata_new;

`ifdef A2C_CDC_JITTER
    // Testbench-only CDC jitter model. When jit_* is set, a first stage holds
    // for one cycle on the edge its source changes from _seen; an unspent
    // release_credit lets the first held transition after reset hold twice.
    logic jit_req, jit_bus_alive;
    logic jit_alive, jit_ack;
    logic req_hold, bus_alive_hold, alive_hold, ack_hold;

    `DFF_INST_DOM(mem_clk, mem_rst_n, logic, req_seen)
    `DFFR_INST_DOM(mem_clk, mem_rst_n, logic, req_release_credit, 1'b1)
    `DFF_INST_DOM(mem_clk, mem_rst_n, logic, bus_alive_seen)
    `DFFR_INST_DOM(mem_clk, mem_rst_n, logic, bus_alive_release_credit, 1'b1)
    `DFFR_INST_DOM(bus_clk, bus_rst_n, logic, alive_seen, 1'b1)
    `DFFR_INST_DOM(bus_clk, bus_rst_n, logic, alive_release_credit, 1'b1)
    `DFFR_INST_DOM(bus_clk, bus_rst_n, logic, ack_seen, 1'b1)
    `DFFR_INST_DOM(bus_clk, bus_rst_n, logic, ack_release_credit, 1'b1)
`endif

    always_comb begin
`ifdef A2C_CDC_JITTER
        req_hold = jit_req && (req_latch != req_seen);
        n_req_sync_meta = req_hold ? req_sync_meta : req_latch;
        n_req_seen = (req_hold && req_release_credit) ? req_seen : req_latch;
        n_req_release_credit = (req_hold && req_release_credit) ? 1'b0 : req_release_credit;
`else
        n_req_sync_meta = req_latch;
`endif
        n_req_sync_stable = req_sync_meta;
`ifdef A2C_CDC_JITTER
        bus_alive_hold = jit_bus_alive && (bus_alive != bus_alive_seen);
        n_bus_alive_sync_meta = bus_alive_hold ? bus_alive_sync_meta : bus_alive;
        n_bus_alive_seen = (bus_alive_hold && bus_alive_release_credit) ? bus_alive_seen : bus_alive;
        n_bus_alive_release_credit = (bus_alive_hold && bus_alive_release_credit) ? 1'b0 : bus_alive_release_credit;
`else
        n_bus_alive_sync_meta = bus_alive;
`endif
        n_bus_alive_sync_mid1 = bus_alive_sync_meta;
        n_bus_alive_sync_mid2 = bus_alive_sync_mid1;
        n_bus_alive_sync_stable = bus_alive_sync_mid2;
`ifdef A2C_CDC_JITTER
        alive_hold = jit_alive && (alive != alive_seen);
        n_alive_sync_meta = alive_hold ? alive_sync_meta : alive;
        n_alive_seen = (alive_hold && alive_release_credit) ? alive_seen : alive;
        n_alive_release_credit = (alive_hold && alive_release_credit) ? 1'b0 : alive_release_credit;
`else
        n_alive_sync_meta = alive;
`endif
        n_alive_sync_stable = alive_sync_meta;
`ifdef A2C_CDC_JITTER
        ack_hold = jit_ack && (ack != ack_seen);
        n_ack_sync_meta = ack_hold ? ack_sync_meta : ack;
        n_ack_seen = (ack_hold && ack_release_credit) ? ack_seen : ack;
        n_ack_release_credit = (ack_hold && ack_release_credit) ? 1'b0 : ack_release_credit;
`else
        n_ack_sync_meta = ack;
`endif
        n_ack_sync_stable = ack_sync_meta;
        n_latched_wr = start_access ? wr : latched_wr;
        n_latched_addr = start_access ? addr : latched_addr;
        n_latched_wdata = start_access ? wdata : latched_wdata;
    end

    always_comb begin
        n_mem_state = mem_state;
        n_err_hold = err_hold;
        n_rdata_hold = rdata_hold;
        mem_port.enable = 1'b0;
        mem_port.wr_en = 1'b0;
        mem_port.addr = '0;
        mem_port.write_data = '0;

        case (mem_state)
            MEM_ARM: begin
                // A request pending here predates the reset: answer it with
                // err without touching the memory.
                if (bus_alive_sync_stable) begin
                    if (!req_sync_stable) begin
                        n_mem_state = MEM_IDLE;
                    end else begin
                        n_err_hold = 1'b1;
                        n_mem_state = MEM_ACKED;
                    end
                end
            end

            MEM_IDLE: begin
                if (req_sync_stable) begin
                    n_mem_state = MEM_ACCESS;
                end
            end

            MEM_ACCESS: begin
                mem_port.enable = 1'b1;
                mem_port.wr_en = latched_wr;
                mem_port.addr = latched_addr;
                mem_port.write_data = latched_wdata;
                if (latched_wr) begin
                    n_err_hold = 1'b0;
                    n_mem_state = MEM_ACKED;
                end else begin
                    n_mem_state = MEM_WAIT_RD;
                end
            end

            MEM_WAIT_RD: begin
                n_rdata_hold = mem_port.read_data;
                n_err_hold = 1'b0;
                n_mem_state = MEM_ACKED;
            end

            MEM_ACKED: begin
                if (!req_sync_stable) begin
                    n_mem_state = MEM_IDLE;
                end
            end

            default: begin
                `qAssertFatal(0, "memory_reg_bridge: mem_state FSM reached an unreachable state")
                n_mem_state = MEM_ARM;
            end
        endcase

        if (!bus_alive_sync_stable) begin
            n_mem_state = MEM_ARM;
        end

        // Launched from n_mem_state, not decoded from mem_state: a
        // synchroniser's first stage must not see a decode glitch.
        n_ack = (n_mem_state == MEM_ACKED);
        n_alive = (n_mem_state == MEM_ARM) ? 1'b0 : (alive | (n_mem_state == MEM_IDLE));
    end

    // req_taken marks the current req level as handled, so a req held past
    // done is not read as a second access.
    always_comb begin
        n_bus_state = bus_state;
        n_req_taken = req_taken;
        n_req_latch = req_latch;
        n_bus_alive = bus_alive;
        start_access = 1'b0;
        done = 1'b0;
        err_new = 1'b0;
        rdata_new = bus_rdata_q;

        if (!req) begin
            n_req_taken = 1'b0;
        end

        case (bus_state)
            BUS_ARM: begin
                if (!alive_sync_stable) begin
                    n_bus_alive = 1'b1;
                    n_bus_state = BUS_CONNECT;
                end
                if (req && !req_taken) begin
                    n_req_taken = 1'b1;
                    done = 1'b1;
                    err_new = 1'b1;
                end
            end

            BUS_CONNECT: begin
                // alive can pulse briefly during a bus reset, so this may exit
                // early; an access started on the pulse drains via BUS_DRAIN.
                if (alive_sync_stable) begin
                    n_bus_state = BUS_IDLE;
                end
                if (req && !req_taken) begin
                    n_req_taken = 1'b1;
                    done = 1'b1;
                    err_new = 1'b1;
                end
            end

            BUS_IDLE: begin
                // Interlock: never start an access against a raised ack.
                if (req && !req_taken && !ack_sync_stable) begin
                    n_req_taken = 1'b1;
                    if (!alive_sync_stable) begin
                        done = 1'b1;
                        err_new = 1'b1;
                    end else begin
                        start_access = 1'b1;
                        n_req_latch = 1'b1;
                        n_bus_state = BUS_WAIT_ACK;
                    end
                end
            end

            BUS_WAIT_ACK: begin
                // On a memory reset, complete with err but hold req_latch
                // until the memory side answers it, so a late ack is not
                // taken for the next access.
                if (!alive_sync_stable) begin
                    done = 1'b1;
                    err_new = 1'b1;
                    n_bus_state = BUS_DRAIN;
                end else if (ack_sync_stable) begin
                    n_req_latch = 1'b0;
                    done = 1'b1;
                    err_new = err_hold;
                    rdata_new = rdata_hold;
                    n_bus_state = BUS_WAIT_ACK_LOW;
                end
            end

            BUS_WAIT_ACK_LOW: begin
                if (!ack_sync_stable) begin
                    n_bus_state = BUS_IDLE;
                end
            end

            BUS_DRAIN: begin
                if (ack_sync_stable) begin
                    n_req_latch = 1'b0;
                    n_bus_state = BUS_WAIT_ACK_LOW;
                end else if (req && !req_taken && !alive_sync_stable) begin
                    n_req_taken = 1'b1;
                    done = 1'b1;
                    err_new = 1'b1;
                end
            end

            default: begin
                `qAssertFatal(0, "memory_reg_bridge: bus_state FSM reached an unreachable state")
                n_bus_state = BUS_ARM;
            end
        endcase

        n_bus_err_q = err_new;
        n_bus_rdata_q = rdata_new;
        err = done ? err_new : bus_err_q;
        rdata = done ? rdata_new : bus_rdata_q;
    end

`ifndef SYNTHESIS
    // These restate the logic above to catch edits and synthesis mismatches;
    // the protocol itself is checked by the testbench monitor. The resets are
    // read as data, which -Wall flags as SYNCASYNCNET under A2C_RESET_ASYNC.
    /* verilator lint_off SYNCASYNCNET */
    always_ff @(posedge bus_clk) begin
        if (bus_rst_n) begin
            `qAssertFatal((done && !err_new) -> (bus_state == BUS_WAIT_ACK && ack_sync_stable),
                          "memory_reg_bridge: a completion without error did not come from an acknowledge")
            `qAssertFatal(req_latch -> !start_access,
                          "memory_reg_bridge: a new access started while a request was still latched")
            `qAssertFatal(start_access -> (bus_state == BUS_IDLE && alive_sync_stable && !ack_sync_stable),
                          "memory_reg_bridge: an access started outside BUS_IDLE with the memory alive and drained")
            `qAssertFatal(bus_alive == (bus_state != BUS_ARM),
                          "memory_reg_bridge: bus_alive is not 0 only in BUS_ARM")
            `qAssertFatal(req_latch -> (bus_state == BUS_WAIT_ACK || bus_state == BUS_DRAIN),
                          "memory_reg_bridge: req_latch is high outside BUS_WAIT_ACK and BUS_DRAIN")
        end
    end

    mem_state_t mem_state_prev;
    logic ack_prev, alive_prev;
    always_ff @(posedge mem_clk) begin
        if (mem_rst_n) begin
            `qAssertFatal(mem_port.enable -> (mem_state == MEM_ACCESS),
                          "memory_reg_bridge: mem_port.enable asserted outside MEM_ACCESS")
            `qAssertFatal((mem_state == MEM_ACCESS) -> (mem_state_prev == MEM_IDLE),
                          "memory_reg_bridge: MEM_ACCESS entered from a state other than MEM_IDLE")
            `qAssertFatal(ack -> (mem_state == MEM_ACKED),
                          "memory_reg_bridge: ack asserted outside MEM_ACKED")
            `qAssertFatal(!((ack && !ack_prev) && (!alive && alive_prev)),
                          "memory_reg_bridge: ack rose on the same edge alive fell")
            `qAssertFatal(((!ack && ack_prev) && (alive && !alive_prev)) ->
                          (mem_state_prev == MEM_ACKED && mem_state == MEM_IDLE),
                          "memory_reg_bridge: ack fell and alive rose on an edge other than MEM_ACKED exiting to the first MEM_IDLE after a reset")
            `qAssertFatal(alive -> (mem_state != MEM_ARM),
                          "memory_reg_bridge: alive asserted in MEM_ARM")
        end
        mem_state_prev <= mem_state;
        ack_prev <= ack;
        alive_prev <= alive;
    end
    /* verilator lint_on SYNCASYNCNET */
`endif

endmodule : memory_reg_bridge
