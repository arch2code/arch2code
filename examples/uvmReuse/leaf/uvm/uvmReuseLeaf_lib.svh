// The library of uvmReuseLeaf: the classes its own bench and a parent's
// bench share. Each variant package includes it in its user span, and a
// parent build compiles those packages too, so the file names nothing of the
// test package or `A2C_UVM_PKG. It names the variant package's in_item_t and
// out_item_t, which a parent's ports of uvmReuseStreamIf share, since every
// rdy_vld_item of uvmReuseBeatSt is one type. Both rundir Makefiles put this
// directory on EXTRA_HDL_INCDIRS. The file has no include guard because it
// declares classes in the including package, and a guard would leave the
// second variant package compiled in the same unit without them.

import a2c_uvm_pkg::*;

`uvm_analysis_imp_decl(_beat_in)
`uvm_analysis_imp_decl(_beat_out)

// Checks the beats on an output against the beats in, through one leaf or
// several in series: each word plus every register in offsets, at the
// mirrored value it had when the beat went in, and last unchanged. The two
// sides are paired in order, whichever monitor writes first: the RTL passes a
// beat from in to out in the same clock, and the model reads it from in
// before it writes out. offsets are uvm_regs, so a parent whose register
// model holds a leaf in a class of its own binds them too. A reset of
// clk_vif's domain drops the beats not yet paired on both sides, so beats a
// parent held between in and out at the reset do not shift the pairing after
// it.
class uvmReuseLeaf_scoreboard extends uvm_scoreboard implements a2c_reset_aware;
    uvm_analysis_imp_beat_in #(in_item_t, uvmReuseLeaf_scoreboard)   in_export;
    uvm_analysis_imp_beat_out #(out_item_t, uvmReuseLeaf_scoreboard) out_export;
    uvm_reg offsets[$];
    virtual a2c_clk_if clk_vif;
    int unsigned checked;
    protected uvmReuseBeatSt expected[$];
    protected uvmReuseBeatSt actual[$];

    `uvm_component_utils(uvmReuseLeaf_scoreboard)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        in_export  = new("in_export", this);
        out_export = new("out_export", this);
    endfunction

    function void write_beat_in(in_item_t it);
        uvmReuseBeatSt e = it.data;
        foreach (offsets[k]) e.word = uvmReuseWordT'(e.word + offsets[k].get_mirrored_value());
        expected.push_back(e);
        pair_beats();
    endfunction

    function void write_beat_out(out_item_t it);
        actual.push_back(it.data);
        pair_beats();
    endfunction

    protected function void pair_beats();
        while (expected.size() != 0 && actual.size() != 0) begin
            uvmReuseBeatSt e = expected.pop_front();
            uvmReuseBeatSt a = actual.pop_front();
            if (a !== e) begin
                `uvm_error("UVM_REUSE_SB", $sformatf("%s: beat %0d is word 'h%0h last %0b, expected word 'h%0h last %0b",
                                                     get_name(), checked, a.word, a.last, e.word, e.last))
            end
            checked++;
        end
    endfunction

    virtual task run_phase(uvm_phase phase);
        if (clk_vif == null) begin
            `uvm_fatal("A2C_CFG", $sformatf("%s: clk_vif is not set", get_full_name()))
        end
        a2c_run_reset_aware(clk_vif, this);
    endtask

    // Nothing to restart at a reset: on_reset() does the work.
    virtual task run_from_reset();
    endtask

    virtual function void on_reset();
        expected.delete();
        actual.delete();
    endfunction

    virtual function void check_phase(uvm_phase phase);
        super.check_phase(phase);
        if (expected.size() != 0 || actual.size() != 0) begin
            `uvm_error("UVM_REUSE_SB", $sformatf("%s: %0d beats in never came out, and %0d came out with no beat in",
                                                 get_name(), expected.size(), actual.size()))
        end
        `uvm_info("UVM_REUSE_SB", $sformatf("%s: %0d beats checked", get_name(), checked), UVM_LOW)
    endfunction
endclass : uvmReuseLeaf_scoreboard

// Sends packets of 1 to max_words words, with last on each packet's final
// beat and 0 to max_gap idle clocks before each beat. plan() draws the
// lengths, so a test can declare the beats() it expects before start().
class uvmReuseLeaf_packet_seq extends uvm_sequence #(in_item_t);
    int unsigned max_words = 8;
    int unsigned max_gap;
    int unsigned lens[$];
    int unsigned idle;

    `uvm_object_utils(uvmReuseLeaf_packet_seq)

    function new(string name = "uvmReuseLeaf_packet_seq");
        super.new(name);
    endfunction

    function void plan(int unsigned packets);
        lens.delete();
        repeat (packets) lens.push_back($urandom_range(max_words, 1));
    endfunction

    function int unsigned beats();
        int unsigned n = 0;
        foreach (lens[p]) n += lens[p];
        return n;
    endfunction

    virtual task body();
        foreach (lens[p]) begin
            for (int unsigned i = 0; i < lens[p]; i++) begin
                in_item_t it = in_item_t::type_id::create("it");
                bit       is_last = i == lens[p] - 1;
                start_item(it);
                // rdy_vld_item's soft gap == 0 would win over a bound alone.
                if (!it.randomize() with { disable soft gap; data.last == local::is_last; gap <= local::max_gap; }) begin
                    `uvm_error("SEQ", "randomize failed")
                end
                idle += it.gap;
                finish_item(it);
            end
        end
        `uvm_info("SEQ", $sformatf("%0d beats sent with %0d idle clocks before them", beats(), idle), UVM_LOW)
    endtask
endclass : uvmReuseLeaf_packet_seq

// Writes offset to the leaf's register block, the model the starter sets
// (seq.model = <reg block>; seq.start(null)), and reads it back. The read
// also holds the starter until the write has reached the DUT.
class uvmReuseLeaf_config_seq extends uvm_reg_sequence;
    uvm_reg_data_t offset = 1;

    `uvm_object_utils(uvmReuseLeaf_config_seq)

    function new(string name = "uvmReuseLeaf_config_seq");
        super.new(name);
    endfunction

    virtual task body();
        uvmReuseLeaf_reg_block m;
        uvm_status_e           status;
        uvm_reg_data_t         readback;
        if (!$cast(m, model)) begin
            `uvm_fatal("A2C_CFG", "uvmReuseLeaf_config_seq needs a uvmReuseLeaf_reg_block model")
        end
        m.offset.write(status, offset, .parent(this));
        if (status != UVM_IS_OK) begin
            `uvm_error("A2C_REG", $sformatf("%s write of 'h%0h returned %s", m.offset.get_full_name(), offset, status.name()))
        end
        m.offset.read(status, readback, .parent(this));
        if (status != UVM_IS_OK || readback != offset) begin
            `uvm_error("A2C_REG", $sformatf("%s read back 'h%0h (%s), wrote 'h%0h", m.offset.get_full_name(), readback,
                                            status.name(), offset))
        end
    endtask
endclass : uvmReuseLeaf_config_seq
