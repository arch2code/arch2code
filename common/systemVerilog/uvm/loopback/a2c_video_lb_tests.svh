// Loopback tests of a2c_video_pkg, on the lb_video_pipe stand-in DUT in
// three families: raw fv/lv in to UG934 axi4_stream out (vid_raw to
// vid_axis_a_out), axi4_stream to axi4_stream (vid_axis_b_in to
// vid_axis_b_out), and rdy_vld to rdy_vld with sof, eol and eof fields and
// a project adapter (vid_rv_in to vid_rv_out), each with a model twin, and
// a fourth with no twin, rdy_vld at one pixel per beat packed into two
// (vid_pk_in to vid_pk_out). lb_vid_base stands in for a generated
// <block>_base_test, and lb_vid_test is the bench's video test that
// `a2c_video_corner_tests expands. Included in a2c_uvm_loopback_pkg after
// a2c_reg_read_lb_tests.svh. Two pixels of 8 bits per beat but on
// vid_pk_in.

`include "../a2c_video_macros.svh"

    typedef struct packed {
        logic            fv;
        logic            lv;
        logic [1:0][7:0] px;
    } lb_vid_raw_t;
    typedef struct packed {
        logic            sof;
        logic            eol;
        logic            eof;
        logic [1:0][7:0] px;
    } lb_vid_beat_t;
    typedef logic [15:0] lb_vid_tdata_t;

    typedef raw_agent #(.data_t(lb_vid_raw_t)) lb_vid_raw_agent_t;
    typedef lb_vid_raw_agent_t::item_t lb_vid_raw_item_t;
    typedef lb_vid_raw_agent_t::config_t lb_vid_raw_config_t;
    typedef virtual raw_if #(.data_t(lb_vid_raw_t)) lb_vid_raw_vif_t;
    typedef axi4_stream_agent #(.tdata_t(lb_vid_tdata_t), .tid_t(logic), .tdest_t(logic), .tuser_t(logic)) lb_vid_axis_agent_t;
    typedef lb_vid_axis_agent_t::item_t lb_vid_axis_item_t;
    typedef lb_vid_axis_agent_t::config_t lb_vid_axis_config_t;
    typedef virtual axi4_stream_if #(.tdata_t(lb_vid_tdata_t), .tid_t(logic), .tdest_t(logic), .tuser_t(logic)) lb_vid_axis_vif_t;
    typedef rdy_vld_agent #(.data_t(lb_vid_beat_t)) lb_vid_rv_agent_t;
    typedef lb_vid_rv_agent_t::item_t lb_vid_rv_item_t;
    typedef lb_vid_rv_agent_t::config_t lb_vid_rv_config_t;
    typedef virtual rdy_vld_if #(.data_t(lb_vid_beat_t)) lb_vid_rv_vif_t;
    typedef axi4_stream_video_adapter #(.tdata_t(lb_vid_tdata_t), .tid_t(logic), .tdest_t(logic), .tuser_t(logic)) lb_vid_axis_adapter_t;

    // What each lb_video_pipe does, indexed by its ID, set by a test. A
    // decided beat is offered from latency + 1 clocks on. The input refuses
    // one clock in every refuse_every, and with accept_every takes one in
    // every accept_every only (0: neither). width_beats is the line
    // the test configured, which configure_dut() sets. The rest are
    // defects, each off at 0: drop the first drop_fv_rise_beats beats of a
    // line that starts on fv rising; no EOL on a line shorter than
    // width_beats; no EOF on a frame the input did not end with one; no SOF
    // on a frame that starts on the clock after the last one ended; count lv
    // high while fv is low as pixels; keep crop_long beats more than
    // width_beats under crop_width; flip bit 0 of pixel 0 of beat flip_beat;
    // on a handshaked input, drop every beat of frame drop_frame_n and of
    // line drop_line_n, counted from 1 over the run, and the EOF of frame
    // drop_eof_n. pass_markers is a correct pipe that passes the input's
    // markers through, so it marks no EOF on a cut frame. drop_lone_beats
    // drops, uncounted, each handshaked beat with SOF, EOL and EOF at once,
    // which a test's other items carry and no planned frame here does.
    typedef enum {LB_VID_A, LB_VID_A_MODEL, LB_VID_B, LB_VID_B_MODEL, LB_VID_C, LB_VID_C_MODEL, LB_VID_D, LB_VID_D_MODEL} lb_vid_pipe_e;
    typedef struct {
        int unsigned latency;
        int unsigned refuse_every;
        int unsigned accept_every;
        int unsigned width_beats;
        bit          crop_width;
        int unsigned crop_long;
        int unsigned drop_fv_rise_beats;
        bit          no_eol_short;
        bit          no_eof_cut;
        bit          merge_b2b;
        bit          lv_vblank_pixels;
        int unsigned flip_beat;
        int unsigned drop_frame_n;
        int unsigned drop_line_n;
        int unsigned drop_eof_n;
        bit          pass_markers;
        bit          drop_lone_beats;
    } lb_vid_pipe_cfg_t;
    lb_vid_pipe_cfg_t lb_vid_pipe_cfg[8] = '{default: '{latency: 2, width_beats: 32, default: 0}};

    typedef enum {LB_VID_RAW_AXIS, LB_VID_AXIS_AXIS, LB_VID_RV_RV, LB_VID_PACK} lb_vid_family_e;

    class lb_vid_raw_adapter extends a2c_video_clocked_adapter #(lb_vid_raw_item_t);
        `uvm_object_utils(lb_vid_raw_adapter)

        function new(string name = "lb_vid_raw_adapter");
            super.new(name);
            pixels_per_beat = 2;
        endfunction

        virtual function void clear(lb_vid_raw_item_t it);
            it.data = '0;
        endfunction

        virtual function void set_frame(lb_vid_raw_item_t it, bit fv, bit sof, bit eof);
            it.data.fv = fv;
        endfunction

        virtual function void set_line(lb_vid_raw_item_t it, bit lv, bit eol);
            it.data.lv = lv;
        endfunction

        virtual function void set_pixel(lb_vid_raw_item_t it, int unsigned p, uvm_bitstream_t v);
            it.data.px[p] = v[7:0];
        endfunction

        virtual function void get_frame(lb_vid_raw_item_t it, output bit fv, output bit sof, output bit eof);
            fv  = it.data.fv;
            sof = 0;
            eof = 0;
        endfunction

        virtual function void get_line(lb_vid_raw_item_t it, output bit lv, output bit eol);
            lv  = it.data.lv;
            eol = 0;
        endfunction

        virtual function uvm_bitstream_t get_pixel(lb_vid_raw_item_t it, int unsigned p);
            return it.data.px[p];
        endfunction
    endclass : lb_vid_raw_adapter

    // A project's adapter for a struct payload with its own markers.
    class lb_vid_rv_adapter extends a2c_video_handshake_adapter #(lb_vid_rv_item_t);
        `uvm_object_utils(lb_vid_rv_adapter)

        function new(string name = "lb_vid_rv_adapter");
            super.new(name);
            has_eof         = 1;
            pixels_per_beat = 2;
        endfunction

        virtual function void clear(lb_vid_rv_item_t it);
            it.data = '0;
        endfunction

        virtual function void set_frame(lb_vid_rv_item_t it, bit fv, bit sof, bit eof);
            it.data.sof = sof;
            it.data.eof = eof;
        endfunction

        virtual function void set_line(lb_vid_rv_item_t it, bit lv, bit eol);
            it.data.eol = eol;
        endfunction

        virtual function void set_pixel(lb_vid_rv_item_t it, int unsigned p, uvm_bitstream_t v);
            it.data.px[p] = v[7:0];
        endfunction

        virtual function void get_frame(lb_vid_rv_item_t it, output bit fv, output bit sof, output bit eof);
            fv  = 1;
            sof = it.data.sof;
            eof = it.data.eof;
        endfunction

        virtual function void get_line(lb_vid_rv_item_t it, output bit lv, output bit eol);
            lv  = 1;
            eol = it.data.eol;
        endfunction

        virtual function uvm_bitstream_t get_pixel(lb_vid_rv_item_t it, int unsigned p);
            return it.data.px[p];
        endfunction
    endclass : lb_vid_rv_adapter

    // The same payload carrying one pixel per beat, in px[0].
    class lb_vid_rv1_adapter extends lb_vid_rv_adapter;
        `uvm_object_utils(lb_vid_rv1_adapter)

        function new(string name = "lb_vid_rv1_adapter");
            super.new(name);
            pixels_per_beat = 1;
        endfunction
    endclass : lb_vid_rv1_adapter

    // Stands in for a generated env: one input agent and one output agent
    // with its counter, for the family the test sets before build.
    class lb_vid_env extends uvm_env;
        virtual a2c_clk_if             clk_vif;
        lb_vid_family_e                family;
        bit                            dual_dut;
        lb_vid_raw_agent_t             raw_in;
        lb_vid_axis_agent_t            axis_in;
        lb_vid_rv_agent_t              rv_in;
        lb_vid_axis_agent_t            axis_out;
        lb_vid_rv_agent_t              rv_out;
        a2c_txn_counter_base           out_counter;
        a2c_txn_counter #(lb_vid_axis_item_t) axis_counter;
        a2c_txn_counter #(lb_vid_rv_item_t)   rv_counter;

        `uvm_component_utils(lb_vid_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected function void get_vif(string pins, ref lb_vid_raw_config_t cfg);
            if (!uvm_config_db#(lb_vid_raw_vif_t)::get(null, "uvm_test_top", pins, cfg.vif)) `uvm_fatal("LB_CFG", {"no interface ", pins})
            if (dual_dut && !uvm_config_db#(lb_vid_raw_vif_t)::get(null, "uvm_test_top", {pins, "_model"}, cfg.model_vif)) `uvm_fatal("LB_CFG", {"no interface ", pins, "_model"})
        endfunction

        protected function lb_vid_axis_agent_t axis_agent(string name, string pins, a2c_role_e role);
            lb_vid_axis_config_t cfg = lb_vid_axis_config_t::type_id::create({name, "_cfg"});
            if (!uvm_config_db#(lb_vid_axis_vif_t)::get(null, "uvm_test_top", pins, cfg.vif)) `uvm_fatal("LB_CFG", {"no interface ", pins})
            if (dual_dut && !uvm_config_db#(lb_vid_axis_vif_t)::get(null, "uvm_test_top", {pins, "_model"}, cfg.model_vif)) `uvm_fatal("LB_CFG", {"no interface ", pins, "_model"})
            cfg.clk_vif   = clk_vif;
            cfg.role      = role;
            cfg.port_name = pins;
            uvm_config_db#(lb_vid_axis_config_t)::set(this, name, "cfg", cfg);
            return lb_vid_axis_agent_t::type_id::create(name, this);
        endfunction

        protected function lb_vid_rv_agent_t rv_agent(string name, string pins, a2c_role_e role);
            lb_vid_rv_config_t cfg = lb_vid_rv_config_t::type_id::create({name, "_cfg"});
            if (!uvm_config_db#(lb_vid_rv_vif_t)::get(null, "uvm_test_top", pins, cfg.vif)) `uvm_fatal("LB_CFG", {"no interface ", pins})
            if (dual_dut && !uvm_config_db#(lb_vid_rv_vif_t)::get(null, "uvm_test_top", {pins, "_model"}, cfg.model_vif)) `uvm_fatal("LB_CFG", {"no interface ", pins, "_model"})
            cfg.clk_vif   = clk_vif;
            cfg.role      = role;
            cfg.port_name = pins;
            uvm_config_db#(lb_vid_rv_config_t)::set(this, name, "cfg", cfg);
            return lb_vid_rv_agent_t::type_id::create(name, this);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(null, "uvm_test_top", "clk", clk_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk'")
            case (family)
                LB_VID_RAW_AXIS: begin
                    lb_vid_raw_config_t cfg = lb_vid_raw_config_t::type_id::create("raw_in_cfg");
                    get_vif("vid_raw", cfg);
                    cfg.clk_vif   = clk_vif;
                    cfg.port_name = "vid_raw";
                    uvm_config_db#(lb_vid_raw_config_t)::set(this, "raw_in", "cfg", cfg);
                    raw_in   = lb_vid_raw_agent_t::type_id::create("raw_in", this);
                    axis_out = axis_agent("axis_out", "vid_axis_a_out", A2C_DST);
                end
                LB_VID_AXIS_AXIS: begin
                    axis_in  = axis_agent("axis_in", "vid_axis_b_in", A2C_SRC);
                    axis_out = axis_agent("axis_out", "vid_axis_b_out", A2C_DST);
                end
                LB_VID_PACK: begin
                    rv_in  = rv_agent("rv_in", "vid_pk_in", A2C_SRC);
                    rv_out = rv_agent("rv_out", "vid_pk_out", A2C_DST);
                end
                default: begin
                    rv_in  = rv_agent("rv_in", "vid_rv_in", A2C_SRC);
                    rv_out = rv_agent("rv_out", "vid_rv_out", A2C_DST);
                end
            endcase
            if (axis_out != null) begin
                axis_counter = a2c_txn_counter#(lb_vid_axis_item_t)::type_id::create("out_counter", this);
                out_counter  = axis_counter;
            end else begin
                rv_counter  = a2c_txn_counter#(lb_vid_rv_item_t)::type_id::create("out_counter", this);
                out_counter = rv_counter;
            end
            out_counter.port_name = "out";
            out_counter.dual      = dual_dut;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            if (axis_counter != null) begin
                axis_out.mon.ap.connect(axis_counter.analysis_export);
                if (dual_dut) axis_out.model_mon.ap.connect(axis_counter.model_export);
            end else begin
                rv_out.mon.ap.connect(rv_counter.analysis_export);
                if (dual_dut) rv_out.model_mon.ap.connect(rv_counter.model_export);
            end
        endfunction

        function uvm_component in_agent();
            if (raw_in != null) return raw_in;
            if (axis_in != null) return axis_in;
            return rv_in;
        endfunction

        function uvm_component out_agent();
            if (axis_out != null) return axis_out;
            return rv_out;
        endfunction
    endclass : lb_vid_env

    // Stands in for a generated <block>_base_test: waits for reset, runs
    // run_body(), waits for the output's expected beats, and holds the run
    // timeout, whose W is stimulus_sent() plus outputs_declared().
    class lb_vid_base extends uvm_test implements a2c_run_work;
        lb_vid_env      env;
        // A name that sorts after "video" builds the env after the video
        // test's video env.
        string          env_name = "env";
        a2c_run_timeout run_timeout;
        int unsigned    output_deadline_cycles = 20000;
        int unsigned    quiet_cycles = 100;
        int             run_timeout_floor_cycles = -1;
        int             run_timeout_factor = -1;

        `uvm_component_utils(lb_vid_base)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (run_timeout_floor_cycles >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_floor_cycles", run_timeout_floor_cycles);
            end
            if (run_timeout_factor >= 0) begin
                uvm_config_db#(int unsigned)::set(this, "run_timeout", "a2c_run_timeout_factor", run_timeout_factor);
            end
            env         = lb_vid_env::type_id::create(env_name, this);
            run_timeout = a2c_run_timeout::type_id::create("run_timeout", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            run_timeout.clk_vif = env.clk_vif;
            run_timeout.clock   = "clk";
            run_timeout.work    = this;
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            env.clk_vif.wait_reset_release();
            run_body();
            env.out_counter.wait_for_count(env.clk_vif, output_deadline_cycles, quiet_cycles);
            phase.drop_objection(this);
        endtask

        virtual task run_body();
        endtask

        virtual function int unsigned stimulus_sent();
            case (env.family)
                LB_VID_RAW_AXIS:  return a2c_items_sent#(lb_vid_raw_item_t)::of(env.raw_in);
                LB_VID_AXIS_AXIS: return a2c_items_sent#(lb_vid_axis_item_t)::of(env.axis_in);
                default:          return a2c_items_sent#(lb_vid_rv_item_t)::of(env.rv_in);
            endcase
        endfunction

        virtual function int unsigned outputs_declared();
            return env.out_counter.declared();
        endfunction
    endclass : lb_vid_base

    // Keeps every A2C_VIDEO, A2C_CFG, A2C_TXN_COUNT, A2C_MODEL_CMP and
    // A2C_RT_* report at UVM_WARNING or above, with its severity, and, with
    // demote set, makes the errors and fatals among them infos.
    class lb_vid_catcher extends uvm_report_catcher;
        bit          demote;
        string       ids[$];
        string       msgs[$];
        uvm_severity sevs[$];

        `uvm_object_utils(lb_vid_catcher)

        function new(string name = "lb_vid_catcher");
            super.new(name);
        endfunction

        virtual function action_e catch();
            string id = get_id();
            if (!(id inside {"A2C_VIDEO", "A2C_CFG", "A2C_TXN_COUNT", "A2C_MODEL_CMP"} || (id.len() > 7 && id.substr(0, 6) == "A2C_RT_"))) return THROW;
            if (get_severity() == UVM_INFO) return THROW;
            ids.push_back(id);
            msgs.push_back(get_message());
            sevs.push_back(get_severity());
            if (demote && get_severity() inside {UVM_ERROR, UVM_FATAL}) begin
                set_severity(UVM_INFO);
                set_action(UVM_DISPLAY);
                set_message({"expected, demoted to info: ", get_message()});
            end
            return THROW;
        endfunction

        function int unsigned count(string id, uvm_severity sev, string sub = "");
            int unsigned n = 0;
            foreach (ids[i]) n += ids[i] == id && sevs[i] == sev && (sub == "" || a2c_contains(msgs[i], sub));
            return n;
        endfunction
    endclass : lb_vid_catcher

    // The bench's video test. A subclass sets family, and the knobs below,
    // in its constructor. want() lists the reports a test expects; with any
    // listed, report_phase passes only on exactly those, and on none at
    // UVM_ERROR or above that it did not list. In Mode A a no_blank or
    // back_to_back test also requires every planned back-to-back beat to be
    // offered so, unless it sets holds_input.
    class lb_vid_test extends a2c_video_test #(lb_vid_base);
        lb_vid_family_e       family = LB_VID_RAW_AXIS;
        bit                   mode_b;
        // The test holds the input sequencer itself, so the driver idles
        // where the plan has no gap.
        bit                   holds_input;
        // Sets a2c_dual_dut while the agents stay single-lane.
        bit                   dual_cfg_only;
        bit                   random_blanking;
        // Raw family: also check the input's framing, which covers the
        // checker's clocked decode.
        bit                   check_input = 1;
        a2c_video_contract    contract;
        lb_vid_catcher        catcher;
        lb_vid_raw_adapter    raw_ad;
        lb_vid_axis_adapter_t axis_ad;
        lb_vid_rv_adapter     rv_ad;
        lb_vid_rv1_adapter    rv1_ad;

        protected string       want_id[$];
        protected uvm_severity want_sev[$];
        protected string       want_sub[$];
        protected int unsigned want_n[$];

        `uvm_component_utils(lb_vid_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function void want(string id, uvm_severity sev, string sub, int unsigned n);
            want_id.push_back(id);
            want_sev.push_back(sev);
            want_sub.push_back(sub);
            want_n.push_back(n);
        endfunction

        // The pipe of a lane.
        function lb_vid_pipe_e pipe(a2c_lane_e lane = A2C_DUT_LANE);
            return lb_vid_pipe_e'(2 * int'(family) + int'(lane));
        endfunction

        virtual function void build_phase(uvm_phase phase);
            catcher = lb_vid_catcher::type_id::create("catcher");
            uvm_report_cb::add(null, catcher);
            raw_ad  = lb_vid_raw_adapter::type_id::create("raw_ad");
            axis_ad = lb_vid_axis_adapter_t::make(8, "axis_ad");
            rv_ad   = lb_vid_rv_adapter::type_id::create("rv_ad");
            rv1_ad  = lb_vid_rv1_adapter::type_id::create("rv1_ad");
            if (contract == null) contract = a2c_video_contract::type_id::create("contract");
            uvm_config_db#(bit)::set(this, "*", "a2c_dual_dut", mode_b || dual_cfg_only);
            super.build_phase(phase);
            env.family   = family;
            env.dual_dut = mode_b;
        endfunction

        virtual function void video_ports();
            case (family)
                LB_VID_RAW_AXIS: begin
                    add_video_input(a2c_video_input#(lb_vid_raw_item_t)::make("vid_raw", raw_ad));
                    add_video_output(a2c_video_output#(lb_vid_axis_item_t)::make("vid_axis_a_out", axis_ad, contract));
                    if (check_input) add_video_output(a2c_video_output#(lb_vid_raw_item_t)::make("vid_raw", raw_ad));
                end
                LB_VID_AXIS_AXIS: begin
                    add_video_input(a2c_video_input#(lb_vid_axis_item_t)::make("vid_axis_b_in", axis_ad));
                    add_video_output(a2c_video_output#(lb_vid_axis_item_t)::make("vid_axis_b_out", axis_ad, contract));
                end
                LB_VID_PACK: begin
                    add_video_input(a2c_video_input#(lb_vid_rv_item_t)::make("vid_pk_in", rv1_ad));
                    add_video_output(a2c_video_output#(lb_vid_rv_item_t)::make("vid_pk_out", rv_ad, contract));
                end
                default: begin
                    add_video_input(a2c_video_input#(lb_vid_rv_item_t)::make("vid_rv_in", rv_ad));
                    add_video_output(a2c_video_output#(lb_vid_rv_item_t)::make("vid_rv_out", rv_ad, contract));
                end
            endcase
        endfunction

        function string out_port();
            case (family)
                LB_VID_RAW_AXIS:  return "vid_axis_a_out";
                LB_VID_AXIS_AXIS: return "vid_axis_b_out";
                LB_VID_PACK:      return "vid_pk_out";
                default:          return "vid_rv_out";
            endcase
        endfunction

        virtual function void video_connect();
            connect_video_input(env.in_agent());
            connect_video_output(out_port(), env.out_agent(), env.out_counter);
            if (family == LB_VID_RAW_AXIS && check_input) connect_video_output("vid_raw", env.raw_in);
        endfunction

        virtual function void configure_video(a2c_video_cfg cfg);
            if (!random_blanking) return;
            cfg.h_blank_min  = cfg.clocked ? 1 : 0;
            cfg.h_blank_max  = 5;
            cfg.v_blank_min  = 1;
            cfg.v_blank_max  = 30;
            cfg.v_front      = $urandom_range(3, 1);
            cfg.v_back       = $urandom_range(3, 0);
            cfg.lead_clocks  = $urandom_range(10, 0);
            cfg.trail_clocks = $urandom_range(10, 1);
        endfunction

        // What a register write does for a real DUT.
        virtual task configure_dut(a2c_video_cfg cfg);
            lb_vid_pipe_cfg[pipe(A2C_DUT_LANE)].width_beats   = cfg.width / 2;
            lb_vid_pipe_cfg[pipe(A2C_MODEL_LANE)].width_beats = cfg.width / 2;
        endtask

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            int unsigned      listed = 0;
            int unsigned      seen = 0;
            super.report_phase(phase);
            foreach (want_id[i]) begin
                int unsigned got = catcher.count(want_id[i], want_sev[i], want_sub[i]);
                if (want_sev[i] != UVM_WARNING) listed += want_n[i];
                if (got != want_n[i]) begin
                    `uvm_error("LB_VID", $sformatf("expected %0d %s %s reports holding '%s', got %0d: %p", want_n[i], want_id[i],
                                                   want_sev[i].name(), want_sub[i], got, catcher.msgs))
                end
            end
            if (!mode_b && !holds_input && video.valid && corner inside {"no_blank", "back_to_back"} && !video.cfg.clocked) begin
                int unsigned planned;
                int unsigned dut;
                int unsigned model;
                bit          two;
                video.in.exactness(planned, dut, model, two);
                if (planned == 0 || dut != planned) begin
                    `uvm_error("LB_VID", $sformatf("corner %s: %0d of %0d planned back-to-back beats offered so in Mode A", corner, dut, planned))
                end
            end
            foreach (catcher.sevs[i]) seen += catcher.sevs[i] inside {UVM_ERROR, UVM_FATAL};
            if (catcher.demote && seen != listed) begin
                `uvm_error("LB_VID", $sformatf("expected %0d errors and fatals in all, got %0d: %p", listed, seen, catcher.msgs))
            end
            `uvm_info("LB_STATS", $sformatf("corner %s, %0d frames planned, %0d idle clocks sent, W %0d", (corner == "") ? "none" : corner,
                                            video.plan.size(), video.idle_sent(), stimulus_sent() + outputs_declared()), UVM_NONE)
            if (srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL) == 0) begin
                `uvm_info("LB_PASS", get_type_name(), UVM_NONE)
            end
        endfunction
    endclass : lb_vid_test

    // The benches: a family, with default blanking or random blanking.
    class lb_vid_a_test extends lb_vid_test;
        `uvm_component_utils(lb_vid_a_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RAW_AXIS;
        endfunction
    endclass : lb_vid_a_test

    class lb_vid_a_rb_test extends lb_vid_a_test;
        `uvm_component_utils(lb_vid_a_rb_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            random_blanking = 1;
        endfunction
    endclass : lb_vid_a_rb_test

    class lb_vid_b_test extends lb_vid_test;
        `uvm_component_utils(lb_vid_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_AXIS_AXIS;
        endfunction
    endclass : lb_vid_b_test

    class lb_vid_b_rb_test extends lb_vid_b_test;
        `uvm_component_utils(lb_vid_b_rb_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            random_blanking = 1;
        endfunction
    endclass : lb_vid_b_rb_test

    class lb_vid_c_test extends lb_vid_test;
        `uvm_component_utils(lb_vid_c_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RV_RV;
        endfunction
    endclass : lb_vid_c_test

    class lb_vid_c_rb_test extends lb_vid_c_test;
        `uvm_component_utils(lb_vid_c_rb_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            random_blanking = 1;
        endfunction
    endclass : lb_vid_c_rb_test

    `a2c_video_corner_tests(lb_vid_a_test)
    `a2c_video_corner_tests(lb_vid_a_rb_test)
    `a2c_video_corner_tests(lb_vid_b_test)
    `a2c_video_corner_tests(lb_vid_b_rb_test)
    `a2c_video_corner_tests(lb_vid_c_test)
    `a2c_video_corner_tests(lb_vid_c_rb_test)

    // Every corner a clocked input allows, and every corner a handshaked one
    // allows; no_blank needs lv to stay high across a line boundary, which a
    // clocked stream cannot carry.
    // LB_TESTS lb_vid_a_test_blanking lb_vid_a_test_back_to_back lb_vid_a_test_short_line lb_vid_a_test_long_line lb_vid_a_test_cut_frame lb_vid_a_test_cut_lv_high lb_vid_a_test_fv_rise_line lb_vid_a_test_lv_vblank lb_vid_a_test_random
    // LB_TESTS lb_vid_a_rb_test_blanking lb_vid_a_rb_test_back_to_back lb_vid_a_rb_test_short_line lb_vid_a_rb_test_long_line lb_vid_a_rb_test_cut_frame lb_vid_a_rb_test_cut_lv_high lb_vid_a_rb_test_fv_rise_line lb_vid_a_rb_test_lv_vblank lb_vid_a_rb_test_random
    // LB_TESTS lb_vid_b_test_blanking lb_vid_b_test_no_blank lb_vid_b_test_back_to_back lb_vid_b_test_short_line lb_vid_b_test_long_line lb_vid_b_test_cut_frame lb_vid_b_test_random
    // LB_TESTS lb_vid_b_rb_test_blanking lb_vid_b_rb_test_no_blank lb_vid_b_rb_test_back_to_back lb_vid_b_rb_test_short_line lb_vid_b_rb_test_long_line lb_vid_b_rb_test_cut_frame lb_vid_b_rb_test_random
    // LB_TESTS lb_vid_c_test_blanking lb_vid_c_test_no_blank lb_vid_c_test_back_to_back lb_vid_c_test_short_line lb_vid_c_test_long_line lb_vid_c_test_cut_frame lb_vid_c_test_random
    // LB_TESTS lb_vid_c_rb_test_blanking lb_vid_c_rb_test_no_blank lb_vid_c_rb_test_back_to_back lb_vid_c_rb_test_short_line lb_vid_c_rb_test_long_line lb_vid_c_rb_test_cut_frame lb_vid_c_rb_test_random

    // A cut frame that ends with EOF on the input (cut_eof) on the rdy_vld
    // family, so the pipe passes the EOF rather than deriving it.
    class vid_cut_eof_test extends lb_vid_c_test;
        `uvm_component_utils(vid_cut_eof_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            corner = "cut_frame";
        endfunction

        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.cut_eof = 1;
        endfunction
    endclass : vid_cut_eof_test

    // A long line cropped to the width by the pipe and by the contract, with
    // pixel values checked exactly.
    class vid_crop_test extends lb_vid_c_test;
        `uvm_component_utils(vid_crop_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            corner = "long_line";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            contract             = a2c_video_contract::type_id::create("contract");
            contract.crop_width  = 1;
            contract.pixel_check = A2C_VIDEO_PIX_EXACT;
            lb_vid_pipe_cfg[LB_VID_C].crop_width = 1;
            super.build_phase(phase);
        endfunction
    endclass : vid_crop_test

    // Each rejection test breaks one validate() rule, so the run stops at
    // end of elaboration with exactly one A2C_CFG fatal that names it, and
    // sends no frame.
    virtual class vid_reject_base extends lb_vid_c_test;
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        pure virtual function string rule();

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            catcher.demote = 1;
            want("A2C_CFG", UVM_FATAL, {"rule ", rule(), ":"}, 1);
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (stimulus_sent() != 0) `uvm_error("LB_VID", $sformatf("a rejected configuration sent %0d items", stimulus_sent()))
        endfunction
    endclass : vid_reject_base

    class vid_reject_geometry_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_geometry_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "geometry";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.width = 63;
        endfunction
    endclass : vid_reject_geometry_test

    class vid_reject_blank_range_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_blank_range_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "blank_range";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.h_blank_min = 5;
            cfg.h_blank_max = 2;
        endfunction
    endclass : vid_reject_blank_range_test

    class vid_reject_clocked_blank_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_clocked_blank_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RAW_AXIS;
        endfunction
        virtual function string rule();
            return "clocked_blank";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.v_blank_min = 0;
        endfunction
    endclass : vid_reject_clocked_blank_test

    class vid_reject_level_corner_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_level_corner_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "level_corner";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.lv_in_vblank = 2;
        endfunction
    endclass : vid_reject_level_corner_test

    class vid_reject_short_line_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_short_line_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "short_line";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.short_line  = 1;
            cfg.short_beats = 32;
        endfunction
    endclass : vid_reject_short_line_test

    class vid_reject_long_line_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_long_line_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "long_line";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.long_line = 1;
        endfunction
    endclass : vid_reject_long_line_test

    class vid_reject_cut_line_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_cut_line_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "cut_line";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.cut_after_line = 7;
        endfunction
    endclass : vid_reject_cut_line_test

    class vid_reject_line_range_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_line_range_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "line_range";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.long_line        = 8;
            cfg.long_extra_beats = 2;
        endfunction
    endclass : vid_reject_line_range_test

    class vid_reject_corner_clash_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_corner_clash_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "corner_clash";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.short_line       = 1;
            cfg.short_beats      = 4;
            cfg.long_line        = 1;
            cfg.long_extra_beats = 2;
        endfunction
    endclass : vid_reject_corner_clash_test

    class vid_reject_corner_frame_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_corner_frame_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "corner_frame";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.back_to_back = 1;
            cfg.corner_frame = 3;
        endfunction
    endclass : vid_reject_corner_frame_test

    // A corner test of the macro whose corner the bench's input cannot
    // carry: the corner's fatal names both the rule and the corner.
    class vid_macro_level_reject_test extends lb_vid_b_test_fv_rise_line;
        `uvm_component_utils(vid_macro_level_reject_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            catcher.demote = 1;
            want("A2C_CFG", UVM_FATAL, "for corner fv_rise_line: 1 broken rule: rule level_corner:", 1);
        endfunction
    endclass : vid_macro_level_reject_test

    class vid_macro_clocked_reject_test extends lb_vid_a_test_no_blank;
        `uvm_component_utils(vid_macro_clocked_reject_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            catcher.demote = 1;
            want("A2C_CFG", UVM_FATAL, "for corner no_blank: 1 broken rule: rule clocked_blank:", 1);
        endfunction
    endclass : vid_macro_clocked_reject_test

    // Each defect test turns on one defect of the pipe under the corner that
    // exposes it, and expects exactly the A2C_VIDEO errors that defect
    // makes, and the A2C_TXN_COUNT error of a defect that changes the beat
    // count. A subclass sets the defect in configure_dut(), after the base's
    // width.
    virtual class vid_defect_base extends lb_vid_test;
        function new(string name, uvm_component parent);
            super.new(name, parent);
            output_deadline_cycles = 2000;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            catcher.demote = 1;
        endfunction
    endclass : vid_defect_base

    // The Q-H class: a line that starts on fv rising loses its first two
    // beats.
    class vid_defect_fv_rise_test extends vid_defect_base;
        `uvm_component_utils(vid_defect_fv_rise_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RAW_AXIS;
            corner = "fv_rise_line";
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_ERROR, "vid_axis_a_out: frame 1 line 0: 60 pixels, expected 64", 1);
            want("A2C_TXN_COUNT", UVM_ERROR, "2 missing", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_A].drop_fv_rise_beats = 2;
        endtask
    endclass : vid_defect_fv_rise_test

    // The short line's beats run on into the next line.
    class vid_defect_no_eol_test extends vid_defect_base;
        `uvm_component_utils(vid_defect_no_eol_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RV_RV;
            corner = "short_line";
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_ERROR, "frame 1: 7 lines, expected 8", 1);
            want("A2C_VIDEO", UVM_ERROR, "frame 1 line 1: 96 pixels, expected 32", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].no_eol_short = 1;
        endtask
    endclass : vid_defect_no_eol_test

    // The same lost EOL under an exact pixel check, which names the line
    // that ran on.
    class vid_defect_run_on_test extends vid_defect_base;
        `uvm_component_utils(vid_defect_run_on_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RV_RV;
            corner = "short_line";
        endfunction
        virtual function void build_phase(uvm_phase phase);
            contract             = a2c_video_contract::type_id::create("contract");
            contract.pixel_check = A2C_VIDEO_PIX_EXACT;
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_ERROR, "frame 1: 7 lines, expected 8", 1);
            want("A2C_VIDEO", UVM_ERROR, "frame 1 line 1: no EOL on its last beat, so line 2 ran on into it with 64 of its 64 pixels", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].no_eol_short = 1;
        endtask
    endclass : vid_defect_run_on_test

    // A cut frame whose input has no EOF goes out with none.
    class vid_defect_no_eof_test extends vid_defect_base;
        `uvm_component_utils(vid_defect_no_eof_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RV_RV;
            corner = "cut_frame";
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_ERROR, "frame 1: no EOF on its last beat; the next frame's SOF came first", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].no_eof_cut = 1;
        endtask
    endclass : vid_defect_no_eof_test

    // The second of two back-to-back frames loses its SOF, on axi4_stream
    // and on raw.
    class vid_defect_merge_test extends vid_defect_base;
        `uvm_component_utils(vid_defect_merge_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_AXIS_AXIS;
            corner = "back_to_back";
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_ERROR, "frame 2: no SOF on its first beat, so its 256 beats in 8 lines came with no frame open", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[pipe()].merge_b2b = 1;
        endtask
    endclass : vid_defect_merge_test

    class vid_defect_merge_raw_test extends vid_defect_merge_test;
        `uvm_component_utils(vid_defect_merge_raw_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RAW_AXIS;
        endfunction
    endclass : vid_defect_merge_raw_test

    // lv high while fv is low comes out as two beats before frame 1 and two
    // after it.
    class vid_defect_lv_vblank_test extends vid_defect_base;
        `uvm_component_utils(vid_defect_lv_vblank_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RAW_AXIS;
            corner = "lv_vblank";
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_ERROR, "2 beats in 1 lines came with no frame open, after frame 0", 1);
            want("A2C_VIDEO", UVM_ERROR, "2 beats in 1 lines came with no frame open, after frame 1", 1);
            want("A2C_TXN_COUNT", UVM_ERROR, "", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_A].lv_vblank_pixels = 1;
        endtask
    endclass : vid_defect_lv_vblank_test

    // The crop keeps one beat past the width.
    class vid_defect_crop_test extends vid_crop_test;
        `uvm_component_utils(vid_defect_crop_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            catcher.demote = 1;
            want("A2C_VIDEO", UVM_ERROR, "frame 1 line 1: 66 pixels, expected 64; the pixels both hold agree", 1);
            want("A2C_TXN_COUNT", UVM_ERROR, "", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].crop_long = 1;
        endtask
    endclass : vid_defect_crop_test

    // One pixel value wrong under A2C_VIDEO_PIX_EXACT: beat 40 is pixels 16
    // and 17 of frame 0's line 1.
    class vid_defect_pixel_test extends vid_crop_test;
        `uvm_component_utils(vid_defect_pixel_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            catcher.demote = 1;
            want("A2C_VIDEO", UVM_ERROR, "frame 0 line 1: pixel x=16 is 'h16, expected 'h17; 1 of 64 pixels differ", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].flip_beat = 40;
        endtask
    endclass : vid_defect_pixel_test

    // Mode B: the model lane's pipe drops the short line's EOL. The model
    // lane's checker and model_cmp fire, and the DUT lane's checker does
    // not.
    class vid_mode_b_model_defect_test extends vid_defect_base;
        `uvm_component_utils(vid_mode_b_model_defect_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RV_RV;
            mode_b = 1;
            corner = "short_line";
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_ERROR, "vid_rv_out model lane: frame 1: 7 lines, expected 8", 1);
            want("A2C_VIDEO", UVM_ERROR, "vid_rv_out model lane: frame 1 line 1: 96 pixels, expected 32", 1);
            want("A2C_VIDEO", UVM_ERROR, "DUT lane", 0);
            want("A2C_MODEL_CMP", UVM_ERROR, "", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C_MODEL].no_eol_short = 1;
        endtask
    endclass : vid_mode_b_model_defect_test

    // Leaves the frames which lists unspecified and checks the pixels of the
    // others exactly.
    class lb_vid_unspecified_contract extends a2c_video_contract;
        int unsigned which[$] = '{1};

        `uvm_object_utils(lb_vid_unspecified_contract)

        function new(string name = "lb_vid_unspecified_contract");
            super.new(name);
            pixel_check = A2C_VIDEO_PIX_EXACT;
        endfunction

        virtual function a2c_video_frame expected_frame(a2c_video_frame in, a2c_video_cfg cfg);
            a2c_video_frame out = super.expected_frame(in, cfg);
            out.unspecified = in.index inside {which};
            return out;
        endfunction
    endclass : lb_vid_unspecified_contract

    // Three 64 x 8 frames on rdy_vld, 256 beats each, frame 1 unspecified
    // and passed through whole by a correct pipe. Its beats are dropped and
    // declared to the counter as they come, and frame 2 is found by its
    // first beat, so nothing fails, and the counter ends with all 768 beats
    // declared.
    class vid_unspecified_test extends lb_vid_c_test;
        int unsigned want_declared = 768;

        `uvm_component_utils(vid_unspecified_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            contract = lb_vid_unspecified_contract::type_id::create("contract");
            super.build_phase(phase);
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (env.out_counter.declared() != want_declared) begin
                `uvm_error("LB_VID", $sformatf("the counter was declared %0d beats, expected %0d", env.out_counter.declared(),
                                               want_declared))
            end
        endfunction
    endclass : vid_unspecified_test

    // The pipe drops the unspecified frame whole, which is no failure either.
    class vid_unspecified_none_test extends vid_unspecified_test;
        `uvm_component_utils(vid_unspecified_none_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_declared = 512;
        endfunction

        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].drop_frame_n = 2;
        endtask
    endclass : vid_unspecified_none_test

    // The pipe flips a pixel of frame 2's first beat, so no beat opens frame
    // 2 and the checker drops the rest of the run, declaring each dropped
    // beat. Frame 2's own 256 beats stay expected, so the run fails twice:
    // one A2C_VIDEO for the frame that never came out and one A2C_TXN_COUNT
    // for its 256 beats.
    class vid_unspecified_next_wrong_test extends vid_unspecified_test;
        `uvm_component_utils(vid_unspecified_next_wrong_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_declared = 1024;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            catcher.demote = 1;
            want("A2C_VIDEO", UVM_ERROR, "vid_rv_out: 1 expected frames never came out, from frame 2, 512 beats dropped waiting for its SOF", 1);
            want("A2C_TXN_COUNT", UVM_ERROR, "expected 1024 transactions, received 768 (256 missing)", 1);
        endfunction

        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].flip_beat = 512;
        endtask
    endclass : vid_unspecified_next_wrong_test

    // The pipe flips a pixel of frame 2's second beat: frame 2 opens on its
    // first beat and fails its pixel check as any frame would.
    class vid_unspecified_next_pixel_test extends vid_unspecified_test;
        `uvm_component_utils(vid_unspecified_next_pixel_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            catcher.demote = 1;
            want("A2C_VIDEO", UVM_ERROR, "frame 2 line 0: pixel x=2", 1);
        endfunction

        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].flip_beat = 513;
        endtask
    endclass : vid_unspecified_next_pixel_test

    // A run the checker cannot skip an unspecified frame in stops with one
    // A2C_CFG fatal, naming why, before any frame is sent.
    virtual class vid_unspecified_reject_base extends vid_unspecified_test;
        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_declared = 0;
        endfunction

        pure virtual function string reason();

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            catcher.demote = 1;
            want("A2C_CFG", UVM_FATAL, reason(), 1);
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (stimulus_sent() != 0) `uvm_error("LB_VID", $sformatf("a rejected run sent %0d items", stimulus_sent()))
        endfunction
    endclass : vid_unspecified_reject_base

    class vid_unspecified_mode_b_test extends vid_unspecified_reject_base;
        `uvm_component_utils(vid_unspecified_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b = 1;
        endfunction

        virtual function string reason();
            return "both lanes run (Mode B)";
        endfunction
    endclass : vid_unspecified_mode_b_test

    class vid_unspecified_unchecked_test extends vid_unspecified_reject_base;
        `uvm_component_utils(vid_unspecified_unchecked_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function string reason();
            return "its pixel check A2C_VIDEO_PIX_UNCHECKED";
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            contract.pixel_check = A2C_VIDEO_PIX_UNCHECKED;
        endfunction
    endclass : vid_unspecified_unchecked_test

    // The last frame is unspecified: its beats are dropped and declared as
    // they come, and the run passes with no frame after it to find.
    class vid_unspecified_last_test extends vid_unspecified_test;
        `uvm_component_utils(vid_unspecified_last_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            lb_vid_unspecified_contract u;
            super.build_phase(phase);
            void'($cast(u, contract));
            u.which = '{2};
        endfunction
    endclass : vid_unspecified_last_test

    // The first frame is unspecified: its beats are dropped and declared as
    // they come, and frame 1 is found by its first beat.
    class vid_unspecified_first_test extends vid_unspecified_test;
        `uvm_component_utils(vid_unspecified_first_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            lb_vid_unspecified_contract u;
            super.build_phase(phase);
            void'($cast(u, contract));
            u.which = '{0};
        endfunction
    endclass : vid_unspecified_first_test

    // Four frames, 1 and 2 unspecified: the checker drops both, declaring
    // their 512 beats as they come, and finds frame 3 by its first beat, so
    // all 1024 beats end up declared.
    class vid_unspecified_two_test extends vid_unspecified_test;
        `uvm_component_utils(vid_unspecified_two_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_declared = 1024;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            lb_vid_unspecified_contract u;
            super.build_phase(phase);
            void'($cast(u, contract));
            u.which = '{1, 2};
        endfunction

        virtual function void configure_video(a2c_video_cfg cfg);
            super.configure_video(cfg);
            cfg.frames = 4;
        endfunction
    endclass : vid_unspecified_two_test

    // Every frame starts with the same beat under A2C_PIX_CONST, so the
    // checker could take the unspecified frame's output for the next frame.
    class vid_unspecified_const_test extends vid_unspecified_reject_base;
        `uvm_component_utils(vid_unspecified_const_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function string reason();
            return "its pixel mode is A2C_PIX_CONST";
        endfunction

        virtual function void configure_video(a2c_video_cfg cfg);
            super.configure_video(cfg);
            cfg.pixel_mode  = A2C_PIX_CONST;
            cfg.pixel_value = 'h5a;
        endfunction
    endclass : vid_unspecified_const_test

    // The frame after the unspecified one carries no SOF, so the checker has
    // nothing to find it by.
    class vid_unspecified_nosof_test extends vid_unspecified_reject_base;
        `uvm_component_utils(vid_unspecified_nosof_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function string reason();
            return "frame 2, the first specified frame after an unspecified one, has no SOF";
        endfunction

        virtual function void edit_plan(a2c_video_cfg cfg, ref a2c_video_frame plan[$]);
            super.edit_plan(cfg, plan);
            plan[2].sof = 0;
        endfunction
    endclass : vid_unspecified_nosof_test

    // An unspecified frame on a clocked output stops the run with A2C_CFG.
    // The raw family checks its clocked input as an output, here under a
    // contract that leaves frame 1 unspecified.
    class vid_unspecified_clocked_test extends lb_vid_a_test;
        lb_vid_unspecified_contract raw_contract;

        `uvm_component_utils(vid_unspecified_clocked_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            raw_contract = lb_vid_unspecified_contract::type_id::create("raw_contract");
            super.build_phase(phase);
            catcher.demote = 1;
            want("A2C_CFG", UVM_FATAL, "this output is clocked", 1);
        endfunction

        virtual function void video_ports();
            add_video_input(a2c_video_input#(lb_vid_raw_item_t)::make("vid_raw", raw_ad));
            add_video_output(a2c_video_output#(lb_vid_axis_item_t)::make("vid_axis_a_out", axis_ad, contract));
            add_video_output(a2c_video_output#(lb_vid_raw_item_t)::make("vid_raw", raw_ad, raw_contract));
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (stimulus_sent() != 0) `uvm_error("LB_VID", $sformatf("a rejected run sent %0d items", stimulus_sent()))
        endfunction
    endclass : vid_unspecified_clocked_test

    // Mode B on raw: every corner a clocked input allows, at random, and the
    // two lanes' input words identical clock for clock.
    class vid_mode_b_raw_test extends lb_vid_a_rb_test_random;
        lb_arrivals #(lb_vid_raw_item_t) dut_in;
        lb_arrivals #(lb_vid_raw_item_t) model_in;

        `uvm_component_utils(vid_mode_b_raw_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b = 1;
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            dut_in   = lb_arrivals#(lb_vid_raw_item_t)::type_id::create("dut_in", this);
            model_in = lb_arrivals#(lb_vid_raw_item_t)::type_id::create("model_in", this);
        endfunction
        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            env.raw_in.mon.ap.connect(dut_in.analysis_export);
            env.raw_in.model_mon.ap.connect(model_in.analysis_export);
        endfunction
        virtual function void check_phase(uvm_phase phase);
            int unsigned differ = 0;
            super.check_phase(phase);
            if (dut_in.items.size() != model_in.items.size() || dut_in.items.size() == 0) begin
                `uvm_error("LB_VID", $sformatf("the lanes saw %0d and %0d input words", dut_in.items.size(), model_in.items.size()))
            end
            foreach (dut_in.items[i]) if (i < model_in.items.size() && !dut_in.items[i].compare(model_in.items[i])) differ++;
            if (differ != 0) `uvm_error("LB_VID", $sformatf("%0d input words differ between the lanes", differ))
        endfunction
    endclass : vid_mode_b_raw_test

    // Mode B on rdy_vld with random corners and blanking, both pipes good.
    class vid_mode_b_pass_test extends lb_vid_c_rb_test_random;
        `uvm_component_utils(vid_mode_b_pass_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b = 1;
        endfunction
    endclass : vid_mode_b_pass_test

    // Mode B on rdy_vld with the DUT lane's pipe taking one clock in four
    // and the model lane's pipe at no latency. The model lane takes each
    // beat up to three clocks before the DUT lane and sends an EOF on two
    // clocks after taking it, so a model-lane frame can end before the
    // sequence has finished sending it, and the checker must hold its plan
    // by then.
    class vid_mode_b_dut_trail_test extends lb_vid_c_test;
        `uvm_component_utils(vid_mode_b_dut_trail_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b = 1;
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].accept_every  = 4;
            lb_vid_pipe_cfg[LB_VID_C_MODEL].latency = 0;
        endtask
    endclass : vid_mode_b_dut_trail_test

    // Mode B on axi4_stream with no blanking, the model lane's pipe refusing
    // every third clock: the model lane trails, so the DUT lane gets idle
    // clocks the plan never asked for, and the corner test warns.
    class vid_mode_b_trail_test extends lb_vid_b_test_no_blank;
        `uvm_component_utils(vid_mode_b_trail_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b = 1;
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_WARNING, "corner no_blank: ", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_B_MODEL].refuse_every = 3;
        endtask
    endclass : vid_mode_b_trail_test

    // Long blanking on a handshaked input with a small run timeout: the
    // budget holds only because stimulus_sent() counts the idle clocks, and
    // W must be the items plus every planned gap.
    class vid_run_timeout_test extends lb_vid_c_test;
        `uvm_component_utils(vid_run_timeout_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            run_timeout_floor_cycles = 50;
            run_timeout_factor       = 1;
            quiet_cycles             = 20;
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.h_blank_min = 40;
            cfg.h_blank_max = 40;
            cfg.v_blank_min = 200;
            cfg.v_blank_max = 200;
        endfunction
        virtual function void check_phase(uvm_phase phase);
            int unsigned gaps = 0;
            int unsigned items = 0;
            super.check_phase(phase);
            foreach (video.plan[f]) begin
                items += video.plan[f].beats(2);
                foreach (video.plan[f].lines[y]) gaps += video.plan[f].lines[y].gap;
            end
            if (gaps == 0 || stimulus_sent() != items + gaps) begin
                `uvm_error("LB_VID", $sformatf("stimulus_sent() is %0d, expected %0d beats and %0d idle clocks", stimulus_sent(), items, gaps))
            end
        endfunction
    endclass : vid_run_timeout_test

    // a2c_rt_checker on a raw input through a2c_video_flow_counts, with
    // a2c_video_unit_rule closing a frame at fv falling on the input and, on
    // the UG934 output, at the EOL that completes the expected frame's
    // lines. A raw input cannot refuse,
    // so a refusal bound of 1 must stay silent. A lag bound below the pipe's
    // latency fires once per frame in the lag variant.
    class vid_rt_raw_test extends lb_vid_a_test;
        typedef a2c_rt_checker #(lb_vid_raw_item_t, lb_vid_axis_item_t) rt_t;
        a2c_video_flow_counts #(lb_vid_raw_item_t) flow;
        rt_t                                        rt;
        int unsigned                                lag = 40;

        `uvm_component_utils(vid_rt_raw_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void build_phase(uvm_phase phase);
            a2c_video_unit_rule #(lb_vid_raw_item_t)  in_rule;
            a2c_video_unit_rule #(lb_vid_axis_item_t) out_rule;
            super.build_phase(phase);
            flow = a2c_video_flow_counts#(lb_vid_raw_item_t)::type_id::create("flow", env);
            rt   = rt_t::type_id::create("rt", env);
            in_rule          = a2c_video_unit_rule#(lb_vid_raw_item_t)::type_id::create("in_rule");
            in_rule.adapter  = raw_ad;
            out_rule         = a2c_video_unit_rule#(lb_vid_axis_item_t)::type_id::create("out_rule");
            out_rule.adapter = axis_ad;
            rt.in_rule    = in_rule;
            rt.out_rule   = out_rule;
            rt.lag_cycles = lag;
            rt.refusal_cycles = 1;
        endfunction
        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            flow.adapter   = raw_ad;
            flow.clk_vif   = env.clk_vif;
            flow.port_name = "vid_raw";
            env.raw_in.mon.ap.connect(flow.analysis_export);
            rt.connect_in(flow);
            rt.connect_out(env.axis_out.mon, env.out_counter, null);
        endfunction
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (rt.units_checked() != video.plan.size()) begin
                `uvm_error("LB_VID", $sformatf("%0d frames checked, expected %0d", rt.units_checked(), video.plan.size()))
            end
        endfunction
    endclass : vid_rt_raw_test

    class vid_rt_raw_lag_test extends vid_rt_raw_test;
        `uvm_component_utils(vid_rt_raw_lag_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            lag = 2;
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            catcher.demote = 1;
            want("A2C_RT_DEADLINE", UVM_ERROR, "has not ended 2 clocks after", 3);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_A].latency = 8;
        endtask
    endclass : vid_rt_raw_lag_test

    // A design that passes framing through: a cut frame with no EOF goes
    // out with none, and the contract takes the markers as received.
    class vid_pass_markers_test extends lb_vid_c_test;
        `uvm_component_utils(vid_pass_markers_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            corner = "cut_frame";
        endfunction
        virtual function void build_phase(uvm_phase phase);
            contract         = a2c_video_contract::type_id::create("contract");
            contract.markers = A2C_VIDEO_MARKERS_AS_RECEIVED;
            super.build_phase(phase);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].pass_markers = 1;
        endtask
    endclass : vid_pass_markers_test

    // The pass-through contract on a pipe that marks EOF on the cut frame,
    // which the input never carried.
    class vid_defect_markers_added_eof_test extends vid_defect_base;
        `uvm_component_utils(vid_defect_markers_added_eof_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RV_RV;
            corner = "cut_frame";
        endfunction
        virtual function void build_phase(uvm_phase phase);
            contract         = a2c_video_contract::type_id::create("contract");
            contract.markers = A2C_VIDEO_MARKERS_AS_RECEIVED;
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_ERROR, "vid_rv_out: frame 1: EOF on its last beat, where the expected frame has none", 1);
        endfunction
    endclass : vid_defect_markers_added_eof_test

    // The pass-through pipe loses frame 0's EOF; the pass-through contract
    // still expects it.
    class vid_defect_markers_lost_eof_test extends vid_defect_base;
        `uvm_component_utils(vid_defect_markers_lost_eof_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RV_RV;
        endfunction
        virtual function void build_phase(uvm_phase phase);
            contract         = a2c_video_contract::type_id::create("contract");
            contract.markers = A2C_VIDEO_MARKERS_AS_RECEIVED;
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_ERROR, "vid_rv_out: frame 0: no EOF on its last beat; the next frame's SOF came first", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].pass_markers = 1;
            lb_vid_pipe_cfg[LB_VID_C].drop_eof_n   = 1;
        endtask
    endclass : vid_defect_markers_lost_eof_test

    // A design that drops frame drop_index: the contract expects nothing of
    // it, and its counter and checker agree.
    class lb_vid_drop_contract extends a2c_video_contract;
        int unsigned drop_index = 1;
        `uvm_object_utils(lb_vid_drop_contract)
        function new(string name = "lb_vid_drop_contract");
            super.new(name);
        endfunction
        virtual function void expected_frames(a2c_video_frame in, a2c_video_cfg cfg, output a2c_video_frame out[$]);
            if (in.index == drop_index) out.delete();
            else super.expected_frames(in, cfg, out);
        endfunction
        virtual function bit preserves_frames();
            return 0;
        endfunction
    endclass : lb_vid_drop_contract

    class vid_drop_frame_test extends lb_vid_c_test;
        `uvm_component_utils(vid_drop_frame_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void build_phase(uvm_phase phase);
            contract = lb_vid_drop_contract::type_id::create("contract");
            super.build_phase(phase);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].drop_frame_n = 2;
        endtask
    endclass : vid_drop_frame_test

    // One pixel per input beat packed two per output beat, on an odd line:
    // each line's last output beat carries one pixel and one of padding.
    class vid_pack_test extends lb_vid_test;
        `uvm_component_utils(vid_pack_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_PACK;
        endfunction
        virtual function void build_phase(uvm_phase phase);
            contract             = a2c_video_contract::type_id::create("contract");
            contract.pixel_check = A2C_VIDEO_PIX_EXACT;
            super.build_phase(phase);
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.width = 63;
        endfunction
    endclass : vid_pack_test

    // The last line of the run never comes out, on a stream with no EOF:
    // the open frame is compared at check_phase.
    class vid_defect_drop_last_line_test extends vid_defect_base;
        `uvm_component_utils(vid_defect_drop_last_line_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_AXIS_AXIS;
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_ERROR, "vid_axis_b_out: frame 2: 7 lines, expected 8; the run ended before the frame did", 1);
            want("A2C_VIDEO", UVM_ERROR, "never came out", 0);
            want("A2C_TXN_COUNT", UVM_ERROR, "", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_B].drop_line_n = 3 * cfg.height;
        endtask
    endclass : vid_defect_drop_last_line_test

    // The last frame never comes out.
    class vid_defect_drop_last_frame_test extends vid_defect_base;
        `uvm_component_utils(vid_defect_drop_last_frame_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family = LB_VID_RV_RV;
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_ERROR, "vid_rv_out: 1 expected frames never came out, from frame 2", 1);
            want("A2C_TXN_COUNT", UVM_ERROR, "", 1);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].drop_frame_n = 3;
        endtask
    endclass : vid_defect_drop_last_frame_test

    // a2c_rt_checker on axi4_stream in and out, neither with EOF, both unit
    // rules closing a frame on the plan's line count; a cut frame and the
    // random corners must keep every unit paired.
    class vid_rt_axis_test extends lb_vid_b_test;
        typedef a2c_rt_checker #(lb_vid_axis_item_t, lb_vid_axis_item_t) rt_t;
        rt_t rt;

        `uvm_component_utils(vid_rt_axis_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void build_phase(uvm_phase phase);
            a2c_video_unit_rule #(lb_vid_axis_item_t) in_rule;
            a2c_video_unit_rule #(lb_vid_axis_item_t) out_rule;
            super.build_phase(phase);
            rt               = rt_t::type_id::create("rt", this);
            in_rule          = a2c_video_unit_rule#(lb_vid_axis_item_t)::type_id::create("in_rule");
            in_rule.adapter  = axis_ad;
            out_rule         = a2c_video_unit_rule#(lb_vid_axis_item_t)::type_id::create("out_rule");
            out_rule.adapter = axis_ad;
            rt.in_rule        = in_rule;
            rt.out_rule       = out_rule;
            rt.lag_cycles     = 40;
            rt.refusal_cycles = 1;
        endfunction
        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            rt.connect_in(env.axis_in.mon);
            rt.connect_out(env.axis_out.mon, env.out_counter, null);
        endfunction
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (rt.units_checked() != video.plan.size()) begin
                `uvm_error("LB_VID", $sformatf("%0d frames checked, expected %0d", rt.units_checked(), video.plan.size()))
            end
        endfunction
    endclass : vid_rt_axis_test

    class vid_rt_axis_cut_test extends vid_rt_axis_test;
        `uvm_component_utils(vid_rt_axis_cut_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            corner = "cut_frame";
        endfunction
    endclass : vid_rt_axis_cut_test

    class vid_rt_axis_random_test extends vid_rt_axis_test;
        `uvm_component_utils(vid_rt_axis_random_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            corner = "random";
        endfunction
    endclass : vid_rt_axis_random_test

    // The env builds after the video env, which must not read it then.
    class vid_build_order_test extends lb_vid_c_test;
        `uvm_component_utils(vid_build_order_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            env_name = "zenv";
            corner   = "cut_frame";
        endfunction
    endclass : vid_build_order_test

    class vid_reject_back_to_back_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_back_to_back_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "back_to_back";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.back_to_back = 1;
            cfg.corner_frame = 2;
        endfunction
    endclass : vid_reject_back_to_back_test

    class vid_reject_cut_last_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_cut_last_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "cut_last";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.cut_after_line = 3;
            cfg.corner_frame   = 2;
        endfunction
    endclass : vid_reject_cut_last_test

    class vid_reject_random_frames_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_random_frames_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "random_frames";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.random_corners = 1;
            cfg.frames         = 2;
        endfunction
    endclass : vid_reject_random_frames_test

    class vid_reject_pixel_value_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_pixel_value_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "pixel_value";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.pixel_mode = A2C_PIX_CONST;
        endfunction
    endclass : vid_reject_pixel_value_test

    // a2c_dual_dut set while the agents have no model_mon: the input's lane
    // watch and the output's model-lane checker each raise A2C_CFG.
    class vid_reject_no_model_mon_test extends vid_defect_base;
        `uvm_component_utils(vid_reject_no_model_mon_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            family        = LB_VID_RV_RV;
            dual_cfg_only = 1;
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            want("A2C_CFG", UVM_ERROR, "has no model-lane monitor model_mon", 2);
        endfunction
    endclass : vid_reject_no_model_mon_test

    // A contract that drops a frame turns off the real-time checker on its
    // output, and only that one.
    class vid_rt_off_scope_test extends vid_drop_frame_test;
        typedef a2c_rt_checker #(lb_vid_rv_item_t, lb_vid_rv_item_t) rt_t;
        rt_t on_out;
        rt_t on_in;

        `uvm_component_utils(vid_rt_off_scope_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            on_out = rt_t::type_id::create("on_out", this);
            on_in  = rt_t::type_id::create("on_in", this);
        endfunction
        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            on_out.connect_in(env.rv_in.mon);
            on_out.connect_out(env.rv_out.mon, env.out_counter, null);
            on_in.connect_out(env.rv_in.mon, null, null);
        endfunction
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (!on_out.off || on_in.off) begin
                `uvm_error("LB_VID", $sformatf("real-time checkers off: on the dropping output %0d, on the input %0d; expected 1 and 0",
                                               on_out.off, on_in.off))
            end
        endfunction
    endclass : vid_rt_off_scope_test

    // Random corners over many short frames: the cuts keep both odd and even
    // line counts.
    class vid_random_cut_parity_test extends lb_vid_c_test_random;
        `uvm_component_utils(vid_random_cut_parity_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.width  = 8;
            cfg.height = 4;
            cfg.frames = 60;
        endfunction
        virtual function void check_phase(uvm_phase phase);
            int unsigned odd = 0;
            int unsigned even = 0;
            super.check_phase(phase);
            foreach (video.plan[f]) begin
                if (!video.plan[f].cut) continue;
                if (video.plan[f].lines.size() % 2) odd++;
                else even++;
            end
            if (odd == 0 || even == 0) begin
                `uvm_error("LB_VID", $sformatf("cut frames kept an odd line count %0d times and an even one %0d times; expected both", odd, even))
            end
        endfunction
    endclass : vid_random_cut_parity_test

    // Mode A under DUT backpressure: every planned back-to-back beat is still
    // offered on the clock after the beat before. The planned beats are the
    // lines' first. The pipe refuses on one clock in four, counted from
    // reset, and a 32-beat line takes 42 or 43 clocks, so the lines' start
    // phases mod 4 cycle through three values, the refused one among them,
    // and every third line starts on a refused clock whatever the first
    // line's phase. One in three would not do: a line takes 48 clocks, 0
    // mod 3, so from the second line on either every line starts on a
    // refused clock or none does, depending on a phase the test does not
    // set.
    class vid_exact_bp_no_blank_test extends lb_vid_c_test_no_blank;
        `uvm_component_utils(vid_exact_bp_no_blank_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].refuse_every = 4;
        endtask
    endclass : vid_exact_bp_no_blank_test

    class vid_exact_bp_b2b_test extends lb_vid_b_test_back_to_back;
        `uvm_component_utils(vid_exact_bp_b2b_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_B].accept_every = 2;
        endtask
    endclass : vid_exact_bp_b2b_test

    // Sends n rdy_vld items that are no video frame: SOF on the first, EOL
    // and EOF on the last, or all three on each with lone, gap idle clocks
    // before each, as another sequence of a test might on the video input's
    // agent.
    class lb_vid_other_seq extends uvm_sequence #(lb_vid_rv_item_t);
        int unsigned n = 40;
        int unsigned gap = 1;
        bit          lone;

        `uvm_object_utils(lb_vid_other_seq)
        function new(string name = "lb_vid_other_seq");
            super.new(name);
        endfunction
        virtual task body();
            for (int unsigned i = 0; i < n; i++) begin
                lb_vid_rv_item_t it = lb_vid_rv_item_t::type_id::create("it");
                start_item(it);
                it.data = '{sof: lone || i == 0, eol: lone || i + 1 == n, eof: lone || i + 1 == n, px: 16'(i)};
                it.gap  = gap;
                finish_item(it);
            end
        endtask
    endclass : lb_vid_other_seq

    // Mode B on rdy_vld with no blanking: 40 other items before the first
    // run and 40 more before a second, each pipe dropping them as frame 1
    // and line 26. Every planned beat goes out on the clock after the beat
    // before on both lanes, and the lane watch must count each one so. With
    // the planned beats counted over the video beats alone, the first
    // run's line-1 beat would be looked for among the other items, which
    // each come after an idle clock.
    class vid_lane_watch_other_items_test extends lb_vid_c_test_no_blank;
        `uvm_component_utils(vid_lane_watch_other_items_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b = 1;
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_WARNING, "planned back-to-back beats", 0);
        endfunction
        virtual task run_body();
            lb_vid_other_seq other  = lb_vid_other_seq::type_id::create("other");
            lb_vid_other_seq other2 = lb_vid_other_seq::type_id::create("other2");
            a2c_video_cfg    c      = new_video_cfg("second");
            if (!video.valid) return;
            configure_dut(video.cfg);
            // Frame 1 is the first run of other items; line 26 is the second,
            // after it and the 3 frames of 8 lines of the first video run.
            lb_vid_pipe_cfg[LB_VID_C].drop_frame_n       = 1;
            lb_vid_pipe_cfg[LB_VID_C].drop_line_n        = 26;
            lb_vid_pipe_cfg[LB_VID_C_MODEL].drop_frame_n = 1;
            lb_vid_pipe_cfg[LB_VID_C_MODEL].drop_line_n  = 26;
            other.start(env.rv_in.sqr);
            send_video();
            other2.start(env.rv_in.sqr);
            c.apply_corner("no_blank");
            send_video(c);
        endtask
        virtual function void report_phase(uvm_phase phase);
            int unsigned planned;
            int unsigned dut;
            int unsigned model;
            int unsigned want_n = 0;
            bit          two;
            video.in.exactness(planned, dut, model, two);
            foreach (video.plan[f]) want_n += video.plan[f].zero_gap_beats.size();
            if (!two || want_n == 0 || planned != want_n || dut != planned || model != planned) begin
                `uvm_error("LB_VID", $sformatf("planned back-to-back beats: %0d in the plan, %0d watched, %0d offered so on the DUT lane and %0d on the model lane",
                                               want_n, planned, dut, model))
            end
            super.report_phase(phase);
        endfunction
    endclass : vid_lane_watch_other_items_test

    // Counts the beats with EOL that the input monitor reports, and fires at
    // the at-th.
    class lb_vid_eol_watch extends uvm_subscriber #(lb_vid_rv_item_t);
        int unsigned at;
        int unsigned n;
        event        fired;

        `uvm_component_utils(lb_vid_eol_watch)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void write(lb_vid_rv_item_t t);
            if (t.data.eol && ++n == at) -> fired;
        endfunction
    endclass : lb_vid_eol_watch

    // Grabs the sequencer for clocks clocks, so the driver idles.
    class lb_vid_hold_seq extends uvm_sequence #(lb_vid_rv_item_t);
        int unsigned       clocks = 5;
        virtual a2c_clk_if clk_vif;

        `uvm_object_utils(lb_vid_hold_seq)
        function new(string name = "lb_vid_hold_seq");
            super.new(name);
        endfunction
        virtual task body();
            grab();
            repeat (clocks) clk_vif.drive_edge();
            ungrab();
        endtask
    endclass : lb_vid_hold_seq

    // Mode A on rdy_vld with no blanking, under DUT backpressure, with the
    // sequencer held for 5 clocks as the third line's last beat transfers.
    // The fourth line's first beat, a planned one, goes out after idle
    // clocks, so the DUT lane gets one planned beat fewer than planned. The
    // lane rendezvous warning is for Mode B, so it must stay silent here.
    class vid_lane_watch_mode_a_test extends lb_vid_c_test_no_blank;
        lb_vid_eol_watch eols;

        `uvm_component_utils(vid_lane_watch_mode_a_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            holds_input = 1;
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            eols    = lb_vid_eol_watch::type_id::create("eols", this);
            eols.at = 3;
            want("A2C_VIDEO", UVM_WARNING, "", 0);
        endfunction
        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            env.rv_in.mon.ap.connect(eols.analysis_export);
        endfunction
        virtual task configure_dut(a2c_video_cfg cfg);
            super.configure_dut(cfg);
            lb_vid_pipe_cfg[LB_VID_C].refuse_every = 4;
        endtask
        virtual task run_body();
            lb_vid_hold_seq hold = lb_vid_hold_seq::type_id::create("hold");
            hold.clk_vif = env.clk_vif;
            fork
                super.run_body();
                begin
                    @(eols.fired);
                    hold.start(env.rv_in.sqr);
                end
            join
        endtask
        virtual function void report_phase(uvm_phase phase);
            int unsigned planned;
            int unsigned dut;
            int unsigned model;
            bit          two;
            video.in.exactness(planned, dut, model, two);
            if (two || planned < 2 || dut + 1 != planned) begin
                `uvm_error("LB_VID", $sformatf("%0d of %0d planned back-to-back beats offered so in Mode A; expected one fewer than planned, the one the hold delayed",
                                               dut, planned))
            end
            super.report_phase(phase);
        endfunction
    endclass : vid_lane_watch_mode_a_test

    // The cut_frame corner's log line names its cut, so a regression entry
    // that moves the cut with +a2c_video_cut_after_line logs a different one.
    class vid_describe_cut_test extends lb_vid_c_test_cut_frame;
        `uvm_component_utils(vid_describe_cut_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (!a2c_contains(video.cfg.describe(), "frame 1 cut after line 3")) begin
                `uvm_error("LB_VID", $sformatf("cut_frame's description names no cut: %s", video.cfg.describe()))
            end
        endfunction
    endclass : vid_describe_cut_test

    // Raises an LB_VID error unless plan frame f has n lines and, with px
    // above 0, its line y has px pixels.
    function automatic void lb_vid_expect_frame(a2c_video_env v, int unsigned f, int unsigned n, int unsigned y = 0,
                                                int unsigned px = 0);
        if (f >= v.plan.size() || v.plan[f].lines.size() != n || (px != 0 && v.plan[f].lines[y].px.size() != px)) begin
            `uvm_error("LB_VID", $sformatf("plan frame %0d: %0d lines, line %0d %0d pixels; expected %0d lines%s", f,
                                           (f < v.plan.size()) ? v.plan[f].lines.size() : 0, y,
                                           (f < v.plan.size() && y < v.plan[f].lines.size()) ? v.plan[f].lines[y].px.size() : 0,
                                           n, (px != 0) ? $sformatf(", %0d pixels", px) : ""))
        end
    endfunction

    // A corner's derived knobs follow the geometry plusargs. cut_frame on 12
    // lines keeps 6, half of them; derived from the default 8 it would keep
    // 4.
    // LB_PLUSARGS vid_corner_height_cut_test +a2c_video_height=12
    class vid_corner_height_cut_test extends lb_vid_c_test_cut_frame;
        `uvm_component_utils(vid_corner_height_cut_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            lb_vid_expect_frame(video, 0, 12);
            lb_vid_expect_frame(video, 1, 6);
        endfunction
    endclass : vid_corner_height_cut_test

    // On 4 lines a cut derived from the default 8 keeps all 4 and breaks
    // rule cut_line; derived from 4 it keeps 2.
    // LB_PLUSARGS vid_corner_height_low_cut_test +a2c_video_height=4
    class vid_corner_height_low_cut_test extends lb_vid_c_test_cut_frame;
        `uvm_component_utils(vid_corner_height_low_cut_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            lb_vid_expect_frame(video, 1, 2);
        endfunction
    endclass : vid_corner_height_low_cut_test

    // short_line's line is half a line of the plusarg's width: 2 beats of 4
    // on 8 pixels, where 16 from the default 64 breaks rule short_line.
    // LB_PLUSARGS vid_corner_width_short_test +a2c_video_width=8
    class vid_corner_width_short_test extends lb_vid_c_test_short_line;
        `uvm_component_utils(vid_corner_width_short_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            lb_vid_expect_frame(video, 1, 8, 1, 4);
        endfunction
    endclass : vid_corner_width_short_test

    // long_line's line is 0 on a frame of one line, where line 1 from the
    // default 8 breaks rule line_range.
    // LB_PLUSARGS vid_corner_height_long_test +a2c_video_height=1
    class vid_corner_height_long_test extends lb_vid_c_test_long_line;
        `uvm_component_utils(vid_corner_height_long_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            lb_vid_expect_frame(video, 1, 1, 0, 68);
        endfunction
    endclass : vid_corner_height_long_test

    // A plusarg naming a corner knob still overrides the corner.
    // LB_PLUSARGS vid_corner_cut_plusarg_test +a2c_video_height=12 +a2c_video_cut_after_line=2
    class vid_corner_cut_plusarg_test extends lb_vid_c_test_cut_frame;
        `uvm_component_utils(vid_corner_cut_plusarg_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            lb_vid_expect_frame(video, 1, 3);
        endfunction
    endclass : vid_corner_cut_plusarg_test

    // The same on cfgs the test sends: one whose corner was applied at the
    // default height cuts at half the plusarg's, and one whose cut the test
    // set after the corner keeps that cut.
    // LB_PLUSARGS vid_corner_sent_cfg_test +a2c_video_height=12
    class vid_corner_sent_cfg_test extends lb_vid_c_test;
        `uvm_component_utils(vid_corner_sent_cfg_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual task run_body();
            a2c_video_cfg follows = new_video_cfg("follows");
            a2c_video_cfg kept    = new_video_cfg("kept");
            if (!video.valid) return;
            configure_dut(video.cfg);
            follows.apply_corner("cut_frame");
            kept.apply_corner("cut_frame");
            kept.cut_after_line = 2;
            send_video(follows);
            send_video(kept);
        endtask
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            lb_vid_expect_frame(video, 1, 6);
            lb_vid_expect_frame(video, 4, 3);
        endfunction
    endclass : vid_corner_sent_cfg_test

    // Mode B on rdy_vld with no blanking, with another sequence sending 40
    // one-beat frames on the same sequencer during the video run, which each
    // pipe drops. The sequencer interleaves them with the video beats, and
    // the lane watch must still find every planned beat on both lanes,
    // offered on the clock after the beat before.
    class vid_lane_watch_concurrent_test extends lb_vid_c_test_no_blank;
        time other_done;
        time video_done;

        `uvm_component_utils(vid_lane_watch_concurrent_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b = 1;
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            want("A2C_VIDEO", UVM_WARNING, "planned back-to-back beats", 0);
        endfunction
        virtual task run_body();
            lb_vid_other_seq other = lb_vid_other_seq::type_id::create("other");
            if (!video.valid) return;
            configure_dut(video.cfg);
            lb_vid_pipe_cfg[LB_VID_C].drop_lone_beats       = 1;
            lb_vid_pipe_cfg[LB_VID_C_MODEL].drop_lone_beats = 1;
            other.lone = 1;
            other.gap  = 0;
            fork
                begin
                    other.start(env.rv_in.sqr);
                    other_done = $time;
                end
                begin
                    send_video();
                    video_done = $time;
                end
            join
        endtask
        virtual function void report_phase(uvm_phase phase);
            int unsigned planned;
            int unsigned dut;
            int unsigned model;
            int unsigned want_n = 0;
            bit          two;
            video.in.exactness(planned, dut, model, two);
            foreach (video.plan[f]) want_n += video.plan[f].zero_gap_beats.size();
            if (!two || want_n == 0 || planned != want_n || dut != planned || model != planned) begin
                `uvm_error("LB_VID", $sformatf("planned back-to-back beats: %0d in the plan, %0d watched, %0d offered so on the DUT lane and %0d on the model lane",
                                               want_n, planned, dut, model))
            end
            if (other_done == 0 || other_done >= video_done) begin
                `uvm_error("LB_VID", $sformatf("the other items ended at %0t and the video run at %0t; expected the other items inside the run",
                                               other_done, video_done))
            end
            super.report_phase(phase);
        endfunction
    endclass : vid_lane_watch_concurrent_test

    // The random corner with cut_eof: every cut frame it draws ends with
    // EOF on the input.
    class vid_random_cut_eof_test extends lb_vid_c_test_random;
        `uvm_component_utils(vid_random_cut_eof_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.width   = 8;
            cfg.height  = 4;
            cfg.frames  = 40;
            cfg.cut_eof = 1;
        endfunction
        virtual function void check_phase(uvm_phase phase);
            int unsigned cuts = 0;
            super.check_phase(phase);
            foreach (video.plan[f]) begin
                if (!video.plan[f].cut) continue;
                cuts++;
                if (!video.plan[f].eof) `uvm_error("LB_VID", $sformatf("random cut frame %0d has no EOF under cut_eof", f))
            end
            if (cuts == 0) `uvm_error("LB_VID", "the random corner drew no cut frame in 40 frames")
        endfunction
    endclass : vid_random_cut_eof_test

    // Raises an LB_VID error for each frame between the first and the last
    // whose corner is not in allowed, and one more if none has a corner.
    function automatic void lb_vid_expect_corners(a2c_video_env v, string allowed[$]);
        int unsigned with_corner = 0;
        foreach (v.plan[f]) begin
            if (f == 0 || f + 1 == v.plan.size()) continue;
            with_corner += v.plan[f].corner != "";
            if (!(v.plan[f].corner_name() inside {allowed})) begin
                `uvm_error("LB_VID", $sformatf("frame %0d drew corner %s, which is not one of %p", f, v.plan[f].corner_name(), allowed))
            end
        end
        if (with_corner == 0) `uvm_error("LB_VID", $sformatf("no frame of %0d drew a corner", v.plan.size()))
    endfunction

    // random_exclude keeps the line lengths equal: the random corner draws
    // no short or long line, and every line is the configured width.
    class vid_random_exclude_test extends lb_vid_c_test_random;
        string allowed[$] = '{"none", "back_to_back", "cut_frame"};
        bit    equal_lines = 1;

        `uvm_component_utils(vid_random_exclude_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.width          = 8;
            cfg.height         = 4;
            cfg.frames         = 40;
            cfg.random_exclude = '{"short_line", "long_line"};
        endfunction
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            lb_vid_expect_corners(video, allowed);
            if (equal_lines) foreach (video.plan[f]) foreach (video.plan[f].lines[y]) begin
                if (video.plan[f].lines[y].px.size() != 8) begin
                    `uvm_error("LB_VID", $sformatf("frame %0d line %0d: %0d pixels, expected 8", f, y, video.plan[f].lines[y].px.size()))
                end
            end
        endfunction
    endclass : vid_random_exclude_test

    // The plusarg's list replaces the test's, and "none" leaves out the
    // plain frame, so every frame between the first and the last draws a
    // short or a long line.
    // LB_PLUSARGS vid_random_exclude_plusarg_test +a2c_video_random_exclude=none,back_to_back,cut_frame
    class vid_random_exclude_plusarg_test extends vid_random_exclude_test;
        `uvm_component_utils(vid_random_exclude_plusarg_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            allowed     = '{"short_line", "long_line"};
            equal_lines = 0;
        endfunction
    endclass : vid_random_exclude_plusarg_test

    // min_cut_lines 5 on 8 lines: every random cut keeps 5 to 7 lines, both
    // odd and even counts among them.
    class vid_random_min_cut_test extends lb_vid_c_test_random;
        int unsigned least = 5;

        `uvm_component_utils(vid_random_min_cut_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.width         = 8;
            cfg.height        = 8;
            cfg.frames        = 40;
            cfg.min_cut_lines = 5;
        endfunction
        virtual function void check_phase(uvm_phase phase);
            int unsigned kept[int unsigned];
            super.check_phase(phase);
            foreach (video.plan[f]) begin
                if (!video.plan[f].cut) continue;
                kept[video.plan[f].lines.size()]++;
                if (video.plan[f].lines.size() < least) begin
                    `uvm_error("LB_VID", $sformatf("random cut frame %0d keeps %0d lines, fewer than %0d", f, video.plan[f].lines.size(), least))
                end
            end
            if (kept.num() == 0) `uvm_error("LB_VID", "the random corner drew no cut frame in 40 frames")
            if (least == 5 && (!kept.exists(6) || !(kept.exists(5) || kept.exists(7)))) begin
                `uvm_error("LB_VID", $sformatf("cut frames kept these line counts: %p; expected both odd and even", kept))
            end
        endfunction
    endclass : vid_random_min_cut_test

    // min_cut_lines 7 on 8 lines from the plusarg: every cut keeps 7 lines,
    // the one count the range holds.
    // LB_PLUSARGS vid_random_min_cut_plusarg_test +a2c_video_min_cut_lines=7
    class vid_random_min_cut_plusarg_test extends vid_random_min_cut_test;
        `uvm_component_utils(vid_random_min_cut_plusarg_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
            least = 7;
        endfunction
    endclass : vid_random_min_cut_plusarg_test

    class vid_reject_random_exclude_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_random_exclude_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "random_exclude";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.random_exclude = '{"blanking"};
        endfunction
    endclass : vid_reject_random_exclude_test

    // Every corner a handshaked input allows, and none, left out.
    class vid_reject_random_pool_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_random_pool_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "random_pool";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.random_corners = 1;
            cfg.random_exclude = '{"none", "back_to_back", "long_line", "short_line", "cut_frame"};
        endfunction
    endclass : vid_reject_random_pool_test

    class vid_reject_min_cut_lines_test extends vid_reject_base;
        `uvm_component_utils(vid_reject_min_cut_lines_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function string rule();
            return "min_cut_lines";
        endfunction
        virtual function void configure_video(a2c_video_cfg cfg);
            cfg.random_corners = 1;
            cfg.min_cut_lines  = 8;
        endfunction
    endclass : vid_reject_min_cut_lines_test

    // Counts the A2C_VIDEO infos that log the contract an output checks.
    class lb_vid_contract_log extends uvm_report_catcher;
        int unsigned n;

        `uvm_object_utils(lb_vid_contract_log)

        function new(string name = "lb_vid_contract_log");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_id() == "A2C_VIDEO" && get_severity() == UVM_INFO && a2c_contains(get_message(), "checks the contract")) n++;
            return THROW;
        endfunction
    endclass : lb_vid_contract_log

    // edit_plan() gives every pixel a value no pixel_mode makes and drops
    // frame 1's last line. The contract, checking pixels exactly, and the
    // output counter must expect the edited frames, and the contract log
    // line still prints once.
    class vid_edit_plan_test extends lb_vid_c_test;
        int unsigned        edits;
        lb_vid_contract_log contract_log;

        `uvm_component_utils(vid_edit_plan_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        static function uvm_bitstream_t edited(int unsigned f, int unsigned y, int unsigned x);
            return 'h5a ^ ((x + 7 * y + 13 * f) & 'hff);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            contract             = a2c_video_contract::type_id::create("contract");
            contract.pixel_check = A2C_VIDEO_PIX_EXACT;
            contract_log         = lb_vid_contract_log::type_id::create("contract_log");
            uvm_report_cb::add(null, contract_log);
            super.build_phase(phase);
        endfunction

        virtual function void edit_plan(a2c_video_cfg cfg, ref a2c_video_frame plan[$]);
            edits++;
            foreach (plan[f]) foreach (plan[f].lines[y]) foreach (plan[f].lines[y].px[x]) plan[f].lines[y].px[x] = edited(f, y, x);
            void'(plan[1].lines.pop_back());
        endfunction

        virtual function void check_phase(uvm_phase phase);
            int unsigned unedited = 0;
            super.check_phase(phase);
            if (edits != 1) `uvm_error("LB_VID", $sformatf("edit_plan() ran %0d times for one run", edits))
            lb_vid_expect_frame(video, 1, 7);
            foreach (video.plan[f]) foreach (video.plan[f].lines[y]) foreach (video.plan[f].lines[y].px[x]) begin
                unedited += video.plan[f].lines[y].px[x] != edited(f, y, x);
            end
            if (unedited != 0) `uvm_error("LB_VID", $sformatf("%0d planned pixels do not hold their edited value", unedited))
            if (contract_log.n != 1) `uvm_error("LB_VID", $sformatf("the contract log line printed %0d times, expected 1", contract_log.n))
        endfunction
    endclass : vid_edit_plan_test

    // edit_plan() edits the queue: it drops frame 1 and appends a frame of
    // two lines with no cfg, which send_video() gives the run's cfg. The
    // contract crops to the cfg's width and checks pixels exactly, and the
    // output counter expects the edited frames' beats.
    class vid_edit_plan_queue_test extends lb_vid_c_test;
        a2c_video_frame appended;

        `uvm_component_utils(vid_edit_plan_queue_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            contract             = a2c_video_contract::type_id::create("contract");
            contract.crop_width  = 1;
            contract.pixel_check = A2C_VIDEO_PIX_EXACT;
            super.build_phase(phase);
        endfunction

        virtual function void edit_plan(a2c_video_cfg cfg, ref a2c_video_frame plan[$]);
            appended       = a2c_video_frame::type_id::create("appended");
            appended.index = 3;
            for (int unsigned y = 0; y < 2; y++) begin
                a2c_video_line l = new();
                l.gap = (y == 0) ? 8 : 2;
                for (int unsigned x = 0; x < cfg.width; x++) l.px.push_back(vid_edit_plan_test::edited(3, y, x));
                appended.lines.push_back(l);
            end
            plan.delete(1);
            plan.push_back(appended);
        endfunction

        virtual function void check_phase(uvm_phase phase);
            int unsigned sent[$];
            super.check_phase(phase);
            foreach (video.plan[f]) sent.push_back(video.plan[f].index);
            if (sent.size() != 3 || sent[0] != 0 || sent[1] != 2 || video.plan[2] != appended) begin
                `uvm_error("LB_VID", $sformatf("the plan sent frames %p; expected 0, 2 and the appended 3", sent))
            end else if (appended.cfg != video.cfg) begin
                `uvm_error("LB_VID", "the appended frame did not get the run's cfg")
            end
            if (outputs_declared() != 576) `uvm_error("LB_VID", $sformatf("the output counter expects %0d beats, not 576", outputs_declared()))
        endfunction
    endclass : vid_edit_plan_queue_test

    // edit_plan() leaves no frame: send_video() raises one A2C_CFG fatal and
    // sends nothing.
    class vid_edit_plan_empty_test extends lb_vid_c_test;
        `uvm_component_utils(vid_edit_plan_empty_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            catcher.demote = 1;
            want("A2C_CFG", UVM_FATAL, "edit_plan() left the run with no frame", 1);
        endfunction
        virtual function void edit_plan(a2c_video_cfg cfg, ref a2c_video_frame plan[$]);
            plan.delete();
        endfunction
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (stimulus_sent() != 0) `uvm_error("LB_VID", $sformatf("an empty plan sent %0d items", stimulus_sent()))
        endfunction
    endclass : vid_edit_plan_empty_test

    // A run planned with make_plan() and sent with in.send() directly, as a
    // bench outside send_video() does: the plan carries its zero_gap_beats,
    // and the lane watch finds every one offered back to back. Marking the
    // plan again leaves it unchanged.
    class vid_direct_send_test extends lb_vid_c_test_no_blank;
        `uvm_component_utils(vid_direct_send_test)
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_body();
            a2c_video_frame p[$];
            if (!video.valid) return;
            configure_dut(video.cfg);
            video.cfg.make_plan(p);
            foreach (video.outs[i]) video.outs[i].counter.expect_count(video.outs[i].expected_beats(p));
            foreach (p[f]) begin
                video.plan.push_back(p[f]);
                video.in.feed(p[f]);
                foreach (video.outs[i]) video.outs[i].feed(p[f]);
            end
            video.in.send(video, video.cfg, p);
        endtask

        virtual function void report_phase(uvm_phase phase);
            int unsigned planned;
            int unsigned dut;
            int unsigned model;
            int unsigned want_n = 0;
            int unsigned again = 0;
            bit          two;
            video.in.exactness(planned, dut, model, two);
            foreach (video.plan[f]) want_n += video.plan[f].zero_gap_beats.size();
            video.cfg.mark_zero_gaps(video.plan);
            foreach (video.plan[f]) again += video.plan[f].zero_gap_beats.size();
            if (want_n == 0 || planned != want_n || dut != planned || again != want_n) begin
                `uvm_error("LB_VID", $sformatf("planned back-to-back beats: %0d in the plan, %0d after marking it again, %0d watched, %0d offered so",
                                               want_n, again, planned, dut))
            end
            super.report_phase(phase);
        endfunction
    endclass : vid_direct_send_test
