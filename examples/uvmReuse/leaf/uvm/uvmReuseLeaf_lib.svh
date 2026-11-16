// The library of uvmReuseLeaf: the classes its own bench and a parent's
// bench share. Each variant package includes it in its user span, and a
// parent build compiles those packages too, so the file names nothing of the
// test package or `A2C_UVM_PKG. Both rundir Makefiles put this directory on
// EXTRA_HDL_INCDIRS. The file has no include guard because it declares
// classes in the including package, and a guard would leave the second
// variant package compiled in the same unit without them.

import a2c_uvm_pkg::*;
import a2c_video_pkg::*;

// uvmReuseVideoIf for a2c_video_pkg: one pixel per beat, the markers in the
// beat. ITEM is the item of the port or connection the adapter serves.
class uvmReuseLeaf_video_adapter #(type ITEM = uvm_sequence_item) extends a2c_video_handshake_adapter #(ITEM);
    `uvm_object_param_utils(uvmReuseLeaf_video_adapter #(ITEM))

    function new(string name = "uvmReuseLeaf_video_adapter");
        super.new(name);
        has_eof    = 1;
        pixel_bits = $bits(uvmReusePixelT);
    endfunction

    virtual function void clear(ITEM it);
        it.data = '0;
    endfunction

    virtual function void set_frame(ITEM it, bit fv, bit sof, bit eof);
        it.data.sof = sof;
        it.data.eof = eof;
    endfunction

    virtual function void set_line(ITEM it, bit lv, bit eol);
        it.data.eol = eol;
    endfunction

    virtual function void set_pixel(ITEM it, int unsigned p, uvm_bitstream_t v);
        it.data.pixel = uvmReusePixelT'(v);
    endfunction

    virtual function void get_frame(ITEM it, output bit fv, output bit sof, output bit eof);
        fv  = 1;
        sof = it.data.sof;
        eof = it.data.eof;
    endfunction

    virtual function void get_line(ITEM it, output bit lv, output bit eol);
        lv  = 1;
        eol = it.data.eol;
    endfunction

    virtual function uvm_bitstream_t get_pixel(ITEM it, int unsigned p);
        return it.data.pixel;
    endfunction
endclass : uvmReuseLeaf_video_adapter

// Each pixel plus the offset register's mirrored value, the markers as
// received. offset is a uvm_reg, so a parent whose model holds the leaf in a
// class of its own binds the contract too.
class uvmReuseLeaf_video_contract extends a2c_video_contract;
    uvm_reg offset;

    `uvm_object_utils(uvmReuseLeaf_video_contract)

    function new(string name = "uvmReuseLeaf_video_contract");
        super.new(name);
        pixel_check = A2C_VIDEO_PIX_EXACT;
        markers     = A2C_VIDEO_MARKERS_AS_RECEIVED;
    endfunction

    virtual function a2c_video_frame expected_frame(a2c_video_frame in, a2c_video_cfg cfg);
        a2c_video_frame out = super.expected_frame(in, cfg);
        uvm_reg_data_t  add = offset.get_mirrored_value();
        foreach (out.lines[y]) foreach (out.lines[y].px[x]) out.lines[y].px[x] = uvmReusePixelT'(out.lines[y].px[x] + add);
        return out;
    endfunction

    virtual function string describe();
        return {super.describe(), ", each pixel plus offset"};
    endfunction
endclass : uvmReuseLeaf_video_contract

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
