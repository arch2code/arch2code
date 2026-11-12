`ifndef A2C_VIDEO_PKG_SV
`define A2C_VIDEO_PKG_SV

`timescale 1ns/1ps

// Video framing stimulus, and an output check that needs no reference model,
// for any block with a video stream port. a2c_video_seq sends frames of a
// configured geometry, with blanking and framing corners, through an adapter
// that maps frame, line and pixel onto the port's item. a2c_video_checker
// rebuilds the frames an output carries through that output's adapter and
// compares them with what a2c_video_contract says a correct DUT makes of the
// frames sent. a2c_video_test adds both to a block's generated base test, and
// `a2c_video_corner_tests, in a2c_video_macros.svh, defines one test per
// corner.
//
// A clocked stream (raw) carries one item per clock and frames it with fv
// and lv levels: a pixel is a clock with both high, a line ends when lv falls
// and a frame when fv falls. A handshaked stream (axi4_stream, rdy_vld)
// marks SOF on a frame's first beat, EOL on a line's last beat and, if it has
// one, EOF on a frame's last beat; its blanking is the item's gap.
package a2c_video_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    typedef enum {A2C_PIX_RAMP, A2C_PIX_RANDOM, A2C_PIX_CONST} a2c_video_pixel_e;

    typedef class a2c_video_adapter_base;
    typedef class a2c_video_cfg;
    typedef class a2c_video_output_base;
    typedef class a2c_video_lane_watch;

    // One line: its pixels, the idle clocks before its first beat, and
    // whether its last beat carries EOL.
    class a2c_video_line;
        uvm_bitstream_t px[$];
        int unsigned    gap;
        bit             eol = 1;

        function a2c_video_line copy();
            a2c_video_line c = new();
            c.px  = px;
            c.gap = gap;
            c.eol = eol;
            return c;
        endfunction
    endclass : a2c_video_line

    // One frame of the plan, of a contract's expectation, or as a checker
    // rebuilt it from an output. The sequence reads the blanking fields; a
    // contract sets index, part, corner, lines and the markers.
    class a2c_video_frame extends uvm_object;
        // The configuration the frame was planned from.
        a2c_video_cfg  cfg;
        int unsigned   index;
        // Which of several expected frames a contract made of one planned
        // frame, or -1 when it made one.
        int            part = -1;
        // The corner applied to this frame, "" for none.
        string         corner = "";
        a2c_video_line lines[$];
        // Whether the first beat carries SOF and the last EOF. A plan frame
        // cut short by cut_after_line on a handshaked stream marks EOF only
        // with cut_eof.
        bit            sof = 1;
        bit            eof = 1;
        bit            cut;
        bit            cut_lv_high;
        bit            back_to_back;
        // Clocked: fv-low clocks before the frame, and fv-high lv-low clocks
        // before its first line and after its last. lv is high on the first
        // lv_after clocks of the next frame's blank and the last lv_before of
        // this one's.
        int unsigned   v_blank;
        int unsigned   v_front;
        int unsigned   v_back;
        int unsigned   lv_before;
        int unsigned   lv_after;
        // Handshaked: the frame's beats, counted from its first, that the plan
        // puts on the clock after the run's beat before. The run's first beat
        // is never one, since nothing in the plan times it against what the
        // test sent before. make_plan() sets it and send_video() sets it
        // again after edit_plan(); a test that edits a plan and calls
        // in.send() itself calls mark_zero_gaps() first.
        int unsigned   zero_gap_beats[$];

        `uvm_object_utils(a2c_video_frame)

        function new(string name = "a2c_video_frame");
            super.new(name);
        endfunction

        // A padded last beat counts as one, as on the pins.
        function int unsigned beats(int unsigned pixels_per_beat);
            int unsigned n = 0;
            foreach (lines[y]) n += (lines[y].px.size() + pixels_per_beat - 1) / pixels_per_beat;
            return n;
        endfunction

        function string corner_name();
            return (corner == "") ? "none" : corner;
        endfunction

        function string label();
            return (part < 0) ? $sformatf("frame %0d", index) : $sformatf("frame %0d part %0d", index, part);
        endfunction
    endclass : a2c_video_frame

    // A frame as it will cross a port, before its first beat: a plan frame
    // on the input, each expected frame on an output. a2c_video_test gives
    // them to the a2c_video_unit_rule of every a2c_rt_checker connected to
    // that port's monitor.
    interface class a2c_video_frame_listener;
        pure virtual function void frame_planned(a2c_video_frame f);
    endclass

    // A framing corner as it applies to one frame.
    typedef struct {
        string       name;
        bit          back_to_back;
        int          short_line;
        int unsigned short_beats;
        int          long_line;
        int unsigned long_extra_beats;
        int          cut_after_line;
        bit          cut_eof;
        bit          cut_lv_high;
        bit          fv_rise_line;
        int unsigned lv_in_vblank;
    } a2c_video_corner_t;

    // The geometry and the corners of a video run, which the sequence, the
    // contract and the checkers all read. A test fills it, the corner a
    // corner test names is applied over that, and +a2c_video_<knob>=<n>
    // overrides both, on the test's cfg at build and on any other cfg when
    // it is sent. The knobs a corner derives from the geometry, such as
    // cut_frame's cut, follow the geometry the plusargs leave unless a test
    // or a plusarg set them. The corner knobs apply to frame corner_frame
    // only, so the frames around it check that the DUT recovers. validate()
    // reports every broken rule in one A2C_CFG fatal.
    class a2c_video_cfg extends uvm_object;
        int unsigned      width = 64;
        int unsigned      height = 8;
        int unsigned      frames = 3;
        int unsigned      corner_frame = 1;
        // A handshaked stream has no item to carry trail clocks, so its run
        // ends with the last beat. A clocked one always ends with fv low.
        int unsigned      lead_clocks = 4;
        int unsigned      trail_clocks = 4;
        // Drawn per gap from [min, max].
        int unsigned      h_blank_min = 2;
        int unsigned      h_blank_max = 2;
        int unsigned      v_blank_min = 8;
        int unsigned      v_blank_max = 8;
        // Clocked only.
        int unsigned      v_front = 1;
        int unsigned      v_back = 1;
        // Handshaked only: 0 to beat_gap_max more idle clocks before every
        // beat.
        int unsigned      beat_gap_max = 0;
        a2c_video_pixel_e pixel_mode = A2C_PIX_RAMP;
        // A2C_PIX_CONST only; X until set, which validate() rejects.
        uvm_bitstream_t   pixel_value;
        // The corners, each off by default.
        bit               back_to_back;
        int               short_line = -1;
        int unsigned      short_beats;
        int               long_line = -1;
        int unsigned      long_extra_beats;
        int               cut_after_line = -1;
        bit               cut_eof;
        bit               cut_lv_high;
        bit               fv_rise_line;
        int unsigned      lv_in_vblank;
        // One corner drawn for each frame but the first and the last, from
        // those the input adapter allows less random_exclude. A cut drawn
        // this way keeps min_cut_lines to height - 1 lines, an odd number
        // and the next an even number, or the reverse, where that range
        // holds both, so a design that tracks line parity across frames
        // meets both. Its cut frames end with EOF when cut_eof is set.
        bit               random_corners;
        // Corners random_corners never draws, by name, with "none" for the
        // plain frame.
        string            random_exclude[$];
        int unsigned      min_cut_lines = 1;
        // Copied from the input adapter by from_adapter().
        bit               clocked;
        bit               has_eof;
        int unsigned      pixels_per_beat = 1;
        int unsigned      pixel_bits = 8;
        // The corner apply_corner() set, which validate() names.
        string            corner = "";

        // The knobs apply_corner() derived from the geometry at the time,
        // which apply_plusargs() derives again from the final geometry.
        protected a2c_video_corner_t derived;

        `uvm_object_utils(a2c_video_cfg)

        function new(string name = "a2c_video_cfg");
            super.new(name);
        endfunction

        function void from_adapter(a2c_video_adapter_base a);
            clocked         = a.clocked;
            has_eof         = a.has_eof;
            pixels_per_beat = a.pixels_per_beat;
            pixel_bits      = a.pixel_bits;
        endfunction

        function int unsigned line_beats();
            return (pixels_per_beat == 0) ? 0 : width / pixels_per_beat;
        endfunction

        // The corner names a corner test may set; a2c_video_macros.svh
        // defines a test for each.
        static function void corner_names(output string names[$]);
            names = '{"blanking", "no_blank", "back_to_back", "short_line", "long_line", "cut_frame", "cut_lv_high",
                      "fv_rise_line", "lv_vblank", "random"};
        endfunction

        // The per-frame knobs of a corner; blanking, no_blank and random change
        // the whole run instead and give none. cut_frame and cut_lv_high cut
        // after line height/2 - 1, so the frame keeps height/2 lines.
        function a2c_video_corner_t corner_knobs(string name);
            a2c_video_corner_t c = '{name: name, short_line: -1, long_line: -1, cut_after_line: -1, default: 0};
            int unsigned       cut = (height >= 2) ? height / 2 - 1 : 0;
            case (name)
                "back_to_back": c.back_to_back = 1;
                "short_line": begin
                    c.short_line  = (height > 1) ? 1 : 0;
                    c.short_beats = line_beats() / 2;
                end
                "long_line": begin
                    c.long_line        = (height > 1) ? 1 : 0;
                    c.long_extra_beats = 2;
                end
                "cut_frame": c.cut_after_line = cut;
                "cut_lv_high": begin
                    c.cut_after_line = cut;
                    c.cut_lv_high    = 1;
                end
                "fv_rise_line": c.fv_rise_line = 1;
                "lv_vblank": c.lv_in_vblank = 2;
                default: c.name = "";
            endcase
            return c;
        endfunction

        // The knobs of corner_frame's corner, as set.
        function a2c_video_corner_t set_knobs();
            return '{name: corner, back_to_back: back_to_back, short_line: short_line, short_beats: short_beats,
                     long_line: long_line, long_extra_beats: long_extra_beats, cut_after_line: cut_after_line,
                     cut_eof: cut_eof, cut_lv_high: cut_lv_high, fv_rise_line: fv_rise_line, lv_in_vblank: lv_in_vblank};
        endfunction

        function void apply_corner(string name);
            a2c_video_corner_t c;
            string             names[$];
            corner = name;
            case (name)
                "blanking": begin
                    h_blank_min  = 1;
                    h_blank_max  = 6;
                    v_blank_min  = 2;
                    v_blank_max  = 24;
                    lead_clocks  = $urandom_range(12, 0);
                    trail_clocks = $urandom_range(12, 1);
                end
                "no_blank": begin
                    h_blank_min = 0;
                    h_blank_max = 0;
                    v_blank_min = 0;
                    v_blank_max = 0;
                    lead_clocks = 0;
                end
                "random": begin
                    random_corners = 1;
                    if (frames < 8) frames = 8;
                end
                default: begin
                    c = corner_knobs(name);
                    if (c.name == "") begin
                        corner_names(names);
                        `uvm_fatal("A2C_CFG", $sformatf("a2c_video_cfg: no corner '%s'; the corners are %p", name, names))
                    end
                    back_to_back     = c.back_to_back;
                    short_line       = c.short_line;
                    short_beats      = c.short_beats;
                    long_line        = c.long_line;
                    long_extra_beats = c.long_extra_beats;
                    cut_after_line   = c.cut_after_line;
                    cut_lv_high      = c.cut_lv_high;
                    fv_rise_line     = c.fv_rise_line;
                    lv_in_vblank     = c.lv_in_vblank;
                    derived          = c;
                end
            endcase
        endfunction

        // A knob still at the value apply_corner() derived follows the
        // geometry; one set since then keeps its value.
        protected function void derive_corner_again();
            a2c_video_corner_t c;
            if (derived.name == "") return;
            c = corner_knobs(derived.name);
            if (short_line == derived.short_line) short_line = c.short_line;
            if (short_beats == derived.short_beats) short_beats = c.short_beats;
            if (long_line == derived.long_line) long_line = c.long_line;
            if (cut_after_line == derived.cut_after_line) cut_after_line = c.cut_after_line;
            derived = c;
        endfunction

        function void apply_plusargs();
            int unsigned mode;
            string       exclude;
            int          from = 0;
            void'($value$plusargs("a2c_video_width=%d", width));
            void'($value$plusargs("a2c_video_height=%d", height));
            void'($value$plusargs("a2c_video_frames=%d", frames));
            void'($value$plusargs("a2c_video_corner_frame=%d", corner_frame));
            void'($value$plusargs("a2c_video_lead_clocks=%d", lead_clocks));
            void'($value$plusargs("a2c_video_trail_clocks=%d", trail_clocks));
            void'($value$plusargs("a2c_video_h_blank_min=%d", h_blank_min));
            void'($value$plusargs("a2c_video_h_blank_max=%d", h_blank_max));
            void'($value$plusargs("a2c_video_v_blank_min=%d", v_blank_min));
            void'($value$plusargs("a2c_video_v_blank_max=%d", v_blank_max));
            void'($value$plusargs("a2c_video_v_front=%d", v_front));
            void'($value$plusargs("a2c_video_v_back=%d", v_back));
            void'($value$plusargs("a2c_video_beat_gap_max=%d", beat_gap_max));
            if ($value$plusargs("a2c_video_pixel_mode=%d", mode)) pixel_mode = a2c_video_pixel_e'(mode);
            // After the geometry, so +a2c_video_height moves a cut_frame cut,
            // and before the corner knobs, which override the corner.
            derive_corner_again();
            void'($value$plusargs("a2c_video_back_to_back=%d", back_to_back));
            void'($value$plusargs("a2c_video_short_line=%d", short_line));
            void'($value$plusargs("a2c_video_short_beats=%d", short_beats));
            void'($value$plusargs("a2c_video_long_line=%d", long_line));
            void'($value$plusargs("a2c_video_long_extra_beats=%d", long_extra_beats));
            void'($value$plusargs("a2c_video_cut_after_line=%d", cut_after_line));
            void'($value$plusargs("a2c_video_cut_eof=%d", cut_eof));
            void'($value$plusargs("a2c_video_cut_lv_high=%d", cut_lv_high));
            void'($value$plusargs("a2c_video_fv_rise_line=%d", fv_rise_line));
            void'($value$plusargs("a2c_video_lv_in_vblank=%d", lv_in_vblank));
            void'($value$plusargs("a2c_video_random_corners=%d", random_corners));
            void'($value$plusargs("a2c_video_min_cut_lines=%d", min_cut_lines));
            // A comma-separated list, which replaces the test's.
            if ($value$plusargs("a2c_video_random_exclude=%s", exclude)) begin
                random_exclude.delete();
                for (int i = 0; i <= exclude.len(); i++) begin
                    if (i < exclude.len() && exclude[i] != ",") continue;
                    if (i > from) random_exclude.push_back(exclude.substr(from, i - 1));
                    from = i + 1;
                end
            end
        endfunction

        // Raises one A2C_CFG fatal naming every broken rule and returns 0, or
        // returns 1.
        function bit validate();
            string       broken[$];
            string       text = "";
            int unsigned beats = line_beats();
            bit          any_corner = back_to_back || short_line >= 0 || long_line >= 0 || cut_after_line >= 0 || fv_rise_line
                                      || lv_in_vblank != 0;
            bit          on_last = !random_corners && corner_frame + 1 == frames;
            string       names[$];
            string       unknown[$];
            string       pool[$];
            string       cuts[$];
            if (width == 0 || height == 0 || frames == 0 || pixels_per_beat == 0 || width % pixels_per_beat != 0) begin
                broken.push_back($sformatf("rule geometry: width %0d, height %0d and frames %0d must be above 0, and width a multiple of the input adapter's %0d pixels per beat",
                                           width, height, frames, pixels_per_beat));
            end
            if (h_blank_min > h_blank_max || v_blank_min > v_blank_max) begin
                broken.push_back($sformatf("rule blank_range: h_blank %0d to %0d and v_blank %0d to %0d must each have min at most max",
                                           h_blank_min, h_blank_max, v_blank_min, v_blank_max));
            end
            if (clocked && (h_blank_min == 0 || v_blank_min == 0)) begin
                broken.push_back($sformatf("rule clocked_blank: on a clocked stream lv must fall between lines and fv between frames, so h_blank_min (%0d) and v_blank_min (%0d) must be at least 1",
                                           h_blank_min, v_blank_min));
            end
            if (!clocked && (fv_rise_line || cut_lv_high || lv_in_vblank != 0)) begin
                broken.push_back("rule level_corner: fv_rise_line, cut_lv_high and lv_in_vblank need fv and lv levels, which a handshaked adapter does not carry; list such a corner only for a clocked input");
            end
            if (short_line >= 0 && (short_beats == 0 || short_beats >= beats)) begin
                broken.push_back($sformatf("rule short_line: short_beats %0d must be 1 or more and below the line's %0d beats",
                                           short_beats, beats));
            end
            if (long_line >= 0 && long_extra_beats == 0) begin
                broken.push_back("rule long_line: long_extra_beats must be 1 or more");
            end
            if ((cut_after_line >= 0 && cut_after_line + 1 >= int'(height)) || (cut_lv_high && cut_after_line < 0)) begin
                broken.push_back($sformatf("rule cut_line: cut_after_line %0d must name a line before the last, %0d, and cut_lv_high needs it",
                                           cut_after_line, int'(height) - 1));
            end
            if (short_line >= int'(height) || long_line >= int'(height)) begin
                broken.push_back($sformatf("rule line_range: short_line %0d and long_line %0d must each be below height %0d",
                                           short_line, long_line, height));
            end
            if ((short_line >= 0 && short_line == long_line)
                    || (cut_after_line >= 0 && (short_line > cut_after_line || long_line > cut_after_line))) begin
                broken.push_back($sformatf("rule corner_clash: short_line %0d and long_line %0d must differ, and neither may follow cut_after_line %0d",
                                           short_line, long_line, cut_after_line));
            end
            if (any_corner && !random_corners && corner_frame >= frames) begin
                broken.push_back($sformatf("rule corner_frame: corner_frame %0d is not one of the %0d frames", corner_frame, frames));
            end
            if (back_to_back && on_last) begin
                broken.push_back($sformatf("rule back_to_back: corner_frame %0d is the last frame, so no frame follows it back to back",
                                           corner_frame));
            end
            if (cut_after_line >= 0 && has_eof && !cut_eof && on_last) begin
                broken.push_back($sformatf("rule cut_last: corner_frame %0d is the last frame of a stream that marks EOF, so with no cut_eof and no next SOF the DUT has nothing to end the cut frame at; cut an earlier frame or set cut_eof",
                                           corner_frame));
            end
            if (random_corners && frames < 3) begin
                broken.push_back($sformatf("rule random_frames: random_corners leaves the first and the last frame plain, so frames %0d must be 3 or more",
                                           frames));
            end
            random_names(names);
            unknown = random_exclude.find(n) with (!(n inside {names}));
            if (unknown.size() != 0) begin
                broken.push_back($sformatf("rule random_exclude: %p names no corner random_corners draws; the names are %p",
                                           unknown, names));
            end
            random_pool(pool);
            cuts = pool.find(n) with (n inside {"cut_frame", "cut_lv_high"});
            if (random_corners && pool.size() == 0) begin
                broken.push_back($sformatf("rule random_pool: random_exclude %p leaves random_corners no corner this geometry and stream allow",
                                           random_exclude));
            end
            if (random_corners && cuts.size() != 0 && (min_cut_lines == 0 || min_cut_lines >= height)) begin
                broken.push_back($sformatf("rule min_cut_lines: min_cut_lines %0d must be 1 or more and below height %0d, since a cut frame keeps fewer lines than a whole one; or exclude cut_frame and cut_lv_high",
                                           min_cut_lines, height));
            end
            if (pixel_mode == A2C_PIX_CONST && pixel_bits != 0 && $isunknown(pixel_value & ((uvm_bitstream_t'(1) << pixel_bits) - 1))) begin
                broken.push_back($sformatf("rule pixel_value: pixel_mode A2C_PIX_CONST needs pixel_value set in its low %0d bits",
                                           pixel_bits));
            end
            if (broken.size() == 0) return 1;
            foreach (broken[i]) text = {text, (i == 0) ? string'("") : "; ", broken[i]};
            `uvm_fatal("A2C_CFG", $sformatf("a2c_video_cfg%s: %0d broken rule%s: %s", (corner == "") ? "" : {" for corner ", corner},
                                            broken.size(), (broken.size() == 1) ? string'("") : "s", text))
            return 0;
        endfunction

        function string describe();
            return $sformatf("%0d frames of %0dx%0d, %0d pixels per beat, h_blank %0d-%0d, v_blank %0d-%0d, lead %0d, trail %0d%s%s",
                             frames, width, height, pixels_per_beat, h_blank_min, h_blank_max, v_blank_min, v_blank_max,
                             lead_clocks, trail_clocks, clocked ? $sformatf(", v_front %0d, v_back %0d", v_front, v_back)
                                                                : $sformatf(", beat_gap_max %0d", beat_gap_max),
                             (cut_after_line >= 0) ? $sformatf(", frame %0d cut after line %0d", corner_frame, cut_after_line) : "");
        endfunction

        protected function uvm_bitstream_t pixel(int unsigned f, int unsigned y, int unsigned x);
            uvm_bitstream_t v;
            case (pixel_mode)
                A2C_PIX_RAMP:   v = x + 7 * y + 13 * f;
                A2C_PIX_RANDOM: v = {$urandom(), $urandom(), $urandom(), $urandom()};
                default:        v = pixel_value;
            endcase
            return v & ((uvm_bitstream_t'(1) << pixel_bits) - 1);
        endfunction

        // The names random_exclude takes: every corner random_corners can
        // draw, and none.
        static function void random_names(output string names[$]);
            names = '{"none", "back_to_back", "long_line", "short_line", "cut_frame", "fv_rise_line", "lv_vblank", "cut_lv_high"};
        endfunction

        // The corners make_plan() draws from for random_corners: those this
        // geometry and the input's stream kind allow, and none ("" here),
        // less random_exclude.
        protected function void random_pool(output string pool[$]);
            string all[$] = '{"", "back_to_back", "long_line"};
            if (height > 1 && line_beats() > 1) all.push_back("short_line");
            if (height >= 2) all.push_back("cut_frame");
            if (clocked) begin
                all.push_back("fv_rise_line");
                all.push_back("lv_vblank");
                if (height >= 2) all.push_back("cut_lv_high");
            end
            pool = all.find(n) with (!(((n == "") ? string'("none") : n) inside {random_exclude}));
        endfunction

        // A random cut_after_line that keeps min_cut_lines to height - 1
        // lines, an odd number of them or an even one, where that range
        // holds both.
        protected function int random_cut(bit odd);
            int unsigned n;
            do n = $urandom_range(height - 1, min_cut_lines);
            while (height - 1 > min_cut_lines && n % 2 != odd);
            return int'(n) - 1;
        endfunction

        // Every frame of the run, with its blanking drawn and its
        // zero_gap_beats set.
        function void make_plan(output a2c_video_frame plan[$]);
            string           pool[$];
            bit              after_b2b = 0;
            int unsigned     prev_lv_after = 0;
            bit              cut_odd = $urandom_range(1, 0);
            random_pool(pool);
            plan.delete();
            for (int unsigned f = 0; f < frames; f++) begin
                a2c_video_corner_t c = corner_knobs("");
                a2c_video_frame    fr = a2c_video_frame::type_id::create($sformatf("frame%0d", f));
                int unsigned       n;
                // The last frame stays plain: a handshaked stream with no EOF
                // ends a cut frame only at the next SOF.
                if (random_corners) begin
                    if (f >= 1 && f + 1 < frames) c = corner_knobs(pool[$urandom_range(pool.size() - 1, 0)]);
                    if (c.cut_after_line >= 0) begin
                        c.cut_after_line = random_cut(cut_odd);
                        c.cut_eof        = cut_eof;
                        cut_odd          = !cut_odd;
                    end
                end else if (f == corner_frame) begin
                    c = set_knobs();
                end
                fr.cfg          = this;
                fr.index        = f;
                fr.corner       = c.name;
                fr.cut          = c.cut_after_line >= 0;
                fr.eof          = !fr.cut || c.cut_eof;
                fr.cut_lv_high  = c.cut_lv_high;
                fr.back_to_back = c.back_to_back;
                fr.lv_before    = c.lv_in_vblank;
                fr.lv_after     = c.lv_in_vblank;
                fr.v_front      = c.fv_rise_line ? 0 : v_front;
                fr.v_back       = (fr.cut && !fr.cut_lv_high) ? $urandom_range(h_blank_max, h_blank_min) : v_back;
                if (f == 0) fr.v_blank = lead_clocks;
                else if (after_b2b) fr.v_blank = clocked ? 1 : 0;
                else fr.v_blank = $urandom_range(v_blank_max, v_blank_min);
                // lv must fall inside the blank between an lv_after run and an
                // lv_before run, so the two never join.
                if (clocked && (prev_lv_after != 0 || fr.lv_before != 0) && fr.v_blank < prev_lv_after + fr.lv_before + 1) begin
                    fr.v_blank = prev_lv_after + fr.lv_before + 1;
                end
                n = fr.cut ? c.cut_after_line + 1 : height;
                for (int unsigned y = 0; y < n; y++) begin
                    a2c_video_line l = new();
                    int unsigned   len = width;
                    if (int'(y) == c.short_line) len = c.short_beats * pixels_per_beat;
                    if (int'(y) == c.long_line) len += c.long_extra_beats * pixels_per_beat;
                    l.gap = (y == 0) ? fr.v_blank : $urandom_range(h_blank_max, h_blank_min);
                    for (int unsigned x = 0; x < len; x++) l.px.push_back(pixel(f, y, x));
                    fr.lines.push_back(l);
                end
                after_b2b     = c.back_to_back;
                prev_lv_after = fr.lv_after;
                plan.push_back(fr);
            end
            mark_zero_gaps(plan);
        endfunction

        // Sets each frame's zero_gap_beats from its lines, replacing what it
        // held: on a handshaked stream with no beat gaps, each line's first
        // beat with no gap, except the run's first beat.
        function void mark_zero_gaps(a2c_video_frame plan[$]);
            foreach (plan[f]) begin
                int unsigned beat = 0;
                plan[f].zero_gap_beats.delete();
                foreach (plan[f].lines[y]) begin
                    if (!clocked && (f != 0 || y != 0) && plan[f].lines[y].gap == 0 && beat_gap_max == 0) begin
                        plan[f].zero_gap_beats.push_back(beat);
                    end
                    beat += (plan[f].lines[y].px.size() + pixels_per_beat - 1) / pixels_per_beat;
                end
            end
        endfunction
    endclass : a2c_video_cfg

    typedef enum {A2C_VIDEO_PIX_UNCHECKED, A2C_VIDEO_PIX_EXACT} a2c_video_pix_check_e;

    // Where an expected frame's SOF, EOL and EOF come from. DERIVED: SOF on
    // the first beat, EOL on each line's last and EOF on the frame's last,
    // whatever the input carried, for a design that owns its framing.
    // AS_RECEIVED: each marker as the input frame carried it, for a
    // streaming design that passes framing through, so a cut frame with no
    // EOF goes out with none.
    typedef enum {A2C_VIDEO_MARKERS_DERIVED, A2C_VIDEO_MARKERS_AS_RECEIVED} a2c_video_markers_e;

    // What a correct DUT outputs for each frame sent, built from the plan and
    // the specification, never from a model. The default makes one frame of
    // each, keeping each line as sent, cut to the configured width under
    // crop_width, with the markers markers selects. A design that scales or
    // crops overrides expected_frame(); one that drops or inserts frames
    // overrides expected_frames(), which may return none or several, and
    // preserves_frames(). One whose output values are a function of its
    // input sets pixel_check to A2C_VIDEO_PIX_EXACT and computes them in
    // expected_frame(). a2c_video_test calls expected_frames() once per
    // planned frame and output: when it plans the run, for an output with a
    // counter on a handshaked stream or with a real-time checker's unit rule;
    // otherwise when the output's first checker takes the frame's plan, just
    // before the frame's first beat. Both are inside send_video(), so the
    // hook may read the frame, the cfg and anything the test set before the
    // run, such as the register mirror, but nothing that changes while the
    // run is sent: register writes made during the run, the DUT's outputs, or
    // the time. The frames it returns are shared by the output's checkers and
    // must not change afterwards.
    class a2c_video_contract extends uvm_object;
        bit                   crop_width;
        a2c_video_pix_check_e pixel_check = A2C_VIDEO_PIX_UNCHECKED;
        a2c_video_markers_e   markers = A2C_VIDEO_MARKERS_DERIVED;

        `uvm_object_utils(a2c_video_contract)

        function new(string name = "a2c_video_contract");
            super.new(name);
        endfunction

        virtual function void expected_frames(a2c_video_frame in, a2c_video_cfg cfg, output a2c_video_frame out[$]);
            out = '{expected_frame(in, cfg)};
        endfunction

        virtual function a2c_video_frame expected_frame(a2c_video_frame in, a2c_video_cfg cfg);
            a2c_video_frame out = a2c_video_frame::type_id::create($sformatf("expected%0d", in.index));
            out.index  = in.index;
            out.corner = in.corner;
            foreach (in.lines[y]) begin
                a2c_video_line l = in.lines[y].copy();
                if (crop_width && l.px.size() > cfg.width) l.px = l.px[0:cfg.width - 1];
                out.lines.push_back(l);
            end
            set_markers(out, in);
            return out;
        endfunction

        // Sets out's markers from in's lines and markers, as markers selects.
        function void set_markers(a2c_video_frame out, a2c_video_frame in);
            bit received = markers == A2C_VIDEO_MARKERS_AS_RECEIVED;
            out.sof = !received || in.sof;
            out.eof = !received || in.eof;
            foreach (out.lines[y]) out.lines[y].eol = !received || y >= in.lines.size() || in.lines[y].eol;
        endfunction

        // A design whose output frames do not follow its input frames one for
        // one returns 0, and the video test turns off the real-time checkers
        // on this output, whose units pair frame with frame.
        virtual function bit preserves_frames();
            return 1;
        endfunction

        virtual function string describe();
            return $sformatf("%s: each frame's lines as sent%s, SOF, EOL and EOF %s, pixel values %s", get_type_name(),
                             crop_width ? string'(", cut to the configured width") : "",
                             (markers == A2C_VIDEO_MARKERS_AS_RECEIVED) ? string'("as received") : "re-derived",
                             (pixel_check == A2C_VIDEO_PIX_EXACT) ? string'("checked") : "not checked");
        endfunction
    endclass : a2c_video_contract

    // What the sequence and the checkers need to know of a port's framing.
    virtual class a2c_video_adapter_base extends uvm_object;
        bit          clocked;
        bit          has_eof;
        int unsigned pixels_per_beat = 1;
        int unsigned pixel_bits = 8;

        function new(string name = "a2c_video_adapter_base");
            super.new(name);
        endfunction

        function uvm_bitstream_t mask(uvm_bitstream_t v);
            return v & ((uvm_bitstream_t'(1) << pixel_bits) - 1);
        endfunction
    endclass : a2c_video_adapter_base

    // Maps frame, line and pixel onto a port's item. The sequence calls
    // clear() and the three setters for every item it sends; each setter gets
    // both the level and the marker, so a clocked adapter writes fv and lv and
    // ignores the markers, and a handshaked one does the opposite. The
    // getters are needed only where a checker reads the stream, and their
    // defaults raise A2C_CFG. Extend a2c_video_handshake_adapter or
    // a2c_video_clocked_adapter rather than this class.
    virtual class a2c_video_adapter #(type ITEM = uvm_sequence_item) extends a2c_video_adapter_base;
        protected bit getter_reported;

        function new(string name = "a2c_video_adapter");
            super.new(name);
        endfunction

        // Sets the payload fields no setter writes.
        virtual function void clear(ITEM it);
        endfunction

        pure virtual function void set_frame(ITEM it, bit fv, bit sof, bit eof);
        pure virtual function void set_line(ITEM it, bit lv, bit eol);
        pure virtual function void set_pixel(ITEM it, int unsigned p, uvm_bitstream_t v);

        // The idle clocks before the item, on a handshaked stream.
        virtual function void set_gap(ITEM it, int unsigned n);
            if (n != 0) begin
                `uvm_fatal("A2C_CFG", $sformatf("%s: the plan puts %0d idle clocks before a beat, but the adapter has no set_gap(); extend a2c_video_handshake_adapter",
                                                get_type_name(), n))
            end
        endfunction

        protected function void no_getter(string which);
            if (getter_reported) return;
            getter_reported = 1;
            `uvm_error("A2C_CFG", $sformatf("%s: a2c_video_checker called %s(), which the adapter does not implement; an adapter on a checked output implements get_frame(), get_line() and get_pixel()",
                                            get_type_name(), which))
        endfunction

        virtual function void get_frame(ITEM it, output bit fv, output bit sof, output bit eof);
            fv  = 0;
            sof = 0;
            eof = 0;
            no_getter("get_frame");
        endfunction

        virtual function void get_line(ITEM it, output bit lv, output bit eol);
            lv  = 0;
            eol = 0;
            no_getter("get_line");
        endfunction

        virtual function uvm_bitstream_t get_pixel(ITEM it, int unsigned p);
            no_getter("get_pixel");
            return 0;
        endfunction
    endclass : a2c_video_adapter

    // For an item with a gap field: axi4_stream, rdy_vld and similar.
    virtual class a2c_video_handshake_adapter #(type ITEM = uvm_sequence_item) extends a2c_video_adapter #(ITEM);
        function new(string name = "a2c_video_handshake_adapter");
            super.new(name);
            clocked = 0;
        endfunction

        virtual function void set_gap(ITEM it, int unsigned n);
            it.gap = n;
        endfunction
    endclass : a2c_video_handshake_adapter

    // For a stream with one item per clock: raw and similar.
    virtual class a2c_video_clocked_adapter #(type ITEM = uvm_sequence_item) extends a2c_video_adapter #(ITEM);
        function new(string name = "a2c_video_clocked_adapter");
            super.new(name);
            clocked = 1;
            has_eof = 0;
        endfunction
    endclass : a2c_video_clocked_adapter

    // Sends the frames of plan through adapter, and writes each frame to plan_ap before the frame's first
    // item. On a clocked stream every blank clock is an item; on a
    // handshaked one the blanking is each item's gap, which idle_sent sums.
    class a2c_video_seq #(type ITEM = uvm_sequence_item) extends uvm_sequence #(ITEM);
        a2c_video_cfg                        cfg;
        a2c_video_adapter #(ITEM)            adapter;
        uvm_analysis_port #(a2c_video_frame) plan_ap;
        a2c_video_frame                      plan[$];
        int unsigned                         idle_sent;
        // Told of each beat as the sequencer grants it.
        a2c_video_lane_watch #(ITEM)         watch;

        `uvm_object_param_utils(a2c_video_seq#(ITEM))

        function new(string name = "a2c_video_seq");
            super.new(name);
        endfunction

        virtual task body();
            int unsigned prev_lv_after = 0;
            if (cfg == null || adapter == null || plan.size() == 0) begin
                `uvm_fatal("A2C_CFG", "a2c_video_seq needs cfg, adapter and plan set before it starts")
            end
            cfg.from_adapter(adapter);
            if (!cfg.validate()) return;
            foreach (plan[f]) begin
                if (plan_ap != null) plan_ap.write(plan[f]);
                if (adapter.clocked) send_clocked(plan[f], prev_lv_after);
                else send_beats(plan[f]);
                prev_lv_after = plan[f].lv_after;
            end
            if (!adapter.clocked) return;
            // The raw driver holds its last item, so the run must end with fv low.
            for (int unsigned c = 0; c < prev_lv_after + ((cfg.trail_clocks == 0) ? 1 : cfg.trail_clocks); c++) begin
                send_clock(0, c < prev_lv_after, null, 0, 0, 0, 0);
            end
        endtask

        protected task send_beats(a2c_video_frame fr);
            int unsigned k = 0;
            int unsigned z = 0;
            foreach (fr.lines[y]) begin
                int unsigned n = (fr.lines[y].px.size() + adapter.pixels_per_beat - 1) / adapter.pixels_per_beat;
                for (int unsigned b = 0; b < n; b++) begin
                    ITEM         it = ITEM::type_id::create("it");
                    bit          last = (b + 1 == n);
                    int unsigned gap = (b == 0) ? fr.lines[y].gap : 0;
                    bit          zero_gap = z < fr.zero_gap_beats.size() && fr.zero_gap_beats[z] == k;
                    if (cfg.beat_gap_max != 0) gap += $urandom_range(cfg.beat_gap_max, 0);
                    z += zero_gap;
                    k++;
                    start_item(it);
                    if (watch != null) watch.granted(zero_gap);
                    adapter.clear(it);
                    adapter.set_frame(it, 1, fr.sof && y == 0 && b == 0, fr.eof && last && y + 1 == fr.lines.size());
                    adapter.set_line(it, 1, last && fr.lines[y].eol);
                    set_pixels(it, fr.lines[y], b);
                    adapter.set_gap(it, gap);
                    idle_sent += gap;
                    finish_item(it);
                end
            end
        endtask

        protected task send_clocked(a2c_video_frame fr, int unsigned prev_lv_after);
            for (int unsigned c = 0; c < fr.v_blank; c++) begin
                send_clock(0, c < prev_lv_after || c + fr.lv_before >= fr.v_blank, null, 0, 0, 0, 0);
            end
            repeat (fr.v_front) send_clock(1, 0, null, 0, 0, 0, 0);
            foreach (fr.lines[y]) begin
                int unsigned n = (fr.lines[y].px.size() + adapter.pixels_per_beat - 1) / adapter.pixels_per_beat;
                if (y != 0) repeat (fr.lines[y].gap) send_clock(1, 0, null, 0, 0, 0, 0);
                for (int unsigned b = 0; b < n; b++) begin
                    send_clock(1, 1, fr.lines[y], b, y == 0 && b == 0, b + 1 == n, b + 1 == n && y + 1 == fr.lines.size());
                end
            end
            // fv falls on the clock after the cut line's last pixel, with lv still high.
            if (fr.cut_lv_high) send_clock(0, 1, null, 0, 0, 0, 0);
            else repeat (fr.v_back) send_clock(1, 0, null, 0, 0, 0, 0);
        endtask

        protected task send_clock(bit fv, bit lv, a2c_video_line l, int unsigned b, bit sof, bit eol, bit eof);
            ITEM it = ITEM::type_id::create("it");
            start_item(it);
            adapter.clear(it);
            adapter.set_frame(it, fv, sof, eof);
            adapter.set_line(it, lv, eol);
            if (l != null) set_pixels(it, l, b);
            finish_item(it);
        endtask

        protected function void set_pixels(ITEM it, a2c_video_line l, int unsigned b);
            for (int unsigned p = 0; p < adapter.pixels_per_beat; p++) begin
                int unsigned x = b * adapter.pixels_per_beat + p;
                adapter.set_pixel(it, p, (x < l.px.size()) ? l.px[x] : uvm_bitstream_t'(0));
            end
        endfunction
    endclass : a2c_video_seq

    `uvm_analysis_imp_decl(_a2c_video_plan)
    `uvm_analysis_imp_decl(_a2c_video_dut)
    `uvm_analysis_imp_decl(_a2c_video_model)

    // The independent output check of one lane of one video output. For each
    // frame the sequence writes to plan_export it takes the zero or more
    // frames the output's contract expects of it, rebuilds the frames on
    // analysis_export through the adapter's getters, and compares them in
    // order: the frame count, lines per frame, pixels per line, the markers
    // the expected frame carries (SOF on the first beat, EOL on each line's
    // last, and EOF on the last where the stream has EOF), and pixel values
    // under A2C_VIDEO_PIX_EXACT. A line whose last beat holds fewer pixels
    // than the beat carries, as UG934 allows, is trimmed to the expected
    // length before the compare.
    //
    // On a handshaked stream SOF opens a frame, or the first beat when the
    // expected frame has no SOF. EOF closes it; without EOF on the stream,
    // or when the expected frame has none, so does the EOL that completes
    // its expected lines; and the next SOF closes it in any case. Beats that
    // come while no frame is open are counted as outside any frame and
    // reported once per run of them; a run of exactly the next expected
    // frame's lines is reported as that frame with no SOF, so the frames
    // after it stay paired. Under an exact pixel check a line that holds the
    // head of the next one, for lack of an EOL, is reported as run on, and
    // the lines after it stay paired too. On a clocked stream fv rising
    // opens a frame, fv falling closes it, lv falling ends a line, lv high
    // with fv low is ignored, and the markers are not compared.
    //
    // Every failure is an A2C_VIDEO UVM_ERROR naming the port and, in Mode
    // B, the lane; the first max_reported print and check_phase counts the
    // rest in one more. check_phase closes a frame still open and compares
    // it, then reports the expected frames that never came out; both name
    // what ended the run.
    class a2c_video_checker #(type ITEM = uvm_sequence_item) extends uvm_component;
        typedef a2c_video_checker #(ITEM) this_t;

        uvm_analysis_imp_a2c_video_plan #(a2c_video_frame, this_t) plan_export;
        uvm_analysis_imp #(ITEM, this_t)                            analysis_export;
        a2c_video_adapter #(ITEM)                                   adapter;
        // Gives the contract's frames for each planned frame.
        a2c_video_output_base                                       owner;
        string                                                      port_name = "";
        int unsigned                                                max_reported = 10;
        // Cleared for a lane that has no monitor to read, which A2C_CFG has
        // reported; the checker then reports nothing.
        bit                                                         enabled = 1;

        protected a2c_video_frame expected[$];
        // The output frame being rebuilt, null while none is open, and its
        // open line.
        protected a2c_video_frame cur;
        protected a2c_video_line  line;
        protected bit             prev_fv;
        protected bit             prev_lv;
        protected int unsigned    strays;
        protected int unsigned    stray_lines;
        protected string          last_label = "";
        protected int unsigned    planned;
        protected int unsigned    expected_n;
        protected int unsigned    frames_out;
        protected int unsigned    lines_out;
        protected int unsigned    beats_out;
        protected int unsigned    frames_bad;
        protected int unsigned    failures;
        protected int unsigned    unprinted;

        `uvm_component_param_utils(a2c_video_checker#(ITEM))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            plan_export     = new("plan_export", this);
            analysis_export = new("analysis_export", this);
            line            = new();
        endfunction

        virtual function void write_a2c_video_plan(a2c_video_frame fr);
            a2c_video_frame e[$];
            owner.expected_for(fr, e);
            foreach (e[i]) expected.push_back(e[i]);
            expected_n += e.size();
            planned++;
        endfunction

        virtual function void write(ITEM t);
            if (adapter.clocked) clocked_item(t);
            else marked_beat(t);
        endfunction

        protected function void fail(string msg);
            failures++;
            if (failures > max_reported) begin
                unprinted++;
                return;
            end
            `uvm_error("A2C_VIDEO", {port_name, ": ", msg})
        endfunction

        protected function void open(bit sof);
            cur     = a2c_video_frame::type_id::create("out");
            cur.sof = sof;
            line    = new();
        endfunction

        protected function void add_pixels(ITEM t);
            for (int unsigned p = 0; p < adapter.pixels_per_beat; p++) line.px.push_back(adapter.mask(adapter.get_pixel(t, p)));
        endfunction

        protected function void end_line(bit eol);
            line.eol = eol;
            cur.lines.push_back(line);
            line = new();
        endfunction

        // The lines the frame now open must hold before it closes on its line
        // count; with no expected frame left, only the next SOF closes it.
        protected function int unsigned lines_due();
            return (expected.size() != 0) ? expected[0].lines.size() : 0;
        endfunction

        // Whether the frame now open closes on its line count rather than at
        // an EOF.
        protected function bit closes_by_count();
            return !adapter.has_eof || (expected.size() != 0 && !expected[0].eof);
        endfunction

        protected function void marked_beat(ITEM t);
            bit fv;
            bit sof;
            bit eof;
            bit lv;
            bit eol;
            adapter.get_frame(t, fv, sof, eof);
            adapter.get_line(t, lv, eol);
            beats_out++;
            if (sof) begin
                flush_strays();
                if (cur != null) close(0, "the next frame's SOF came first");
                open(1);
            end else if (cur == null) begin
                if (strays == 0 && expected.size() != 0 && !expected[0].sof) begin
                    open(0);
                end else begin
                    strays++;
                    stray_lines += eol;
                    return;
                end
            end
            add_pixels(t);
            if (eol) end_line(1);
            if (adapter.has_eof && eof) close(1, "");
            else if (eol && closes_by_count() && cur.lines.size() == lines_due()) close(0, "");
        endfunction

        protected function void clocked_item(ITEM t);
            bit fv;
            bit sof;
            bit eof;
            bit lv;
            bit eol;
            adapter.get_frame(t, fv, sof, eof);
            adapter.get_line(t, lv, eol);
            if (fv && !prev_fv) open(1);
            if (cur != null) begin
                if (prev_fv && prev_lv && !(fv && lv) && line.px.size() != 0) end_line(1);
                if (fv && lv) begin
                    add_pixels(t);
                    beats_out++;
                end
                if (prev_fv && !fv) close(0, "");
            end
            prev_fv = fv;
            prev_lv = lv;
        endfunction

        protected function void flush_strays();
            if (strays == 0) return;
            if (expected.size() != 0 && stray_lines != 0 && stray_lines == expected[0].lines.size()) begin
                a2c_video_frame e = expected.pop_front();
                fail($sformatf("%s: no SOF on its first beat, so its %0d beats in %0d lines came with no frame open",
                               e.label(), strays, stray_lines));
                frames_bad++;
                last_label = e.label();
            end else begin
                fail($sformatf("%0d beats in %0d lines came with no frame open, %s", strays, stray_lines,
                               (last_label == "") ? "before the first frame" : {"after ", last_label}));
            end
            strays      = 0;
            stray_lines = 0;
        endfunction

        // A line left open ends the frame; on a handshaked stream it lacks
        // its EOL.
        protected function void close(bit got_eof, string why);
            if (line.px.size() != 0) end_line(adapter.clocked);
            cur.eof = got_eof;
            frames_out++;
            lines_out += cur.lines.size();
            compare(cur, why);
            cur = null;
        endfunction

        // Under an exact pixel check, whether the pixels of o past the first
        // n are the head of the expected line next: a lost EOL that ran the
        // next line, or the part of it that came, on into this one.
        protected function bit runs_on(a2c_video_line o, int unsigned n, a2c_video_line next);
            if (o.px.size() - n > next.px.size()) return 0;
            for (int unsigned i = n; i < o.px.size(); i++) begin
                if (o.px[i] != adapter.mask(next.px[i - n])) return 0;
            end
            return 1;
        endfunction

        // Trims the padding of a last beat that holds fewer pixels than the
        // beat carries: o keeps want pixels when it has exactly the beats
        // those need.
        protected function void trim(a2c_video_line o, int unsigned want);
            int unsigned ppb = adapter.pixels_per_beat;
            if (want != 0 && o.px.size() > want && o.px.size() == (want + ppb - 1) / ppb * ppb) o.px = o.px[0:want - 1];
        endfunction

        protected function void compare(a2c_video_frame out, string why);
            a2c_video_frame e;
            string          name;
            string          sfx = (why == "") ? "" : {"; ", why};
            int unsigned    errors = failures;
            int unsigned    y;
            int unsigned    j = 0;
            int unsigned    run_ons = 0;
            bit             exact;
            if (expected.size() == 0) begin
                fail($sformatf("output frame %0d of %0d lines came with no expected frame left%s", frames_out - 1, out.lines.size(), sfx));
                frames_bad++;
                return;
            end
            e          = expected.pop_front();
            name       = e.label();
            last_label = name;
            exact      = owner.contract.pixel_check == A2C_VIDEO_PIX_EXACT;
            if (out.lines.size() != e.lines.size()) begin
                fail($sformatf("%s: %0d lines, expected %0d%s", name, out.lines.size(), e.lines.size(), sfx));
                exact = 0;
            end
            if (!adapter.clocked && out.sof != e.sof) begin
                fail(out.sof ? $sformatf("%s: SOF on its first beat, where the expected frame has none", name)
                             : $sformatf("%s: no SOF on its first beat", name));
            end
            // j is the expected line that output line y is held to; a line
            // that ran on into the one before moves it one further.
            for (y = 0; y < out.lines.size() && j < e.lines.size(); y++, j++) begin
                a2c_video_line o = out.lines[y];
                a2c_video_line w = e.lines[j];
                int            first = -1;
                int unsigned   differ = 0;
                trim(o, w.px.size());
                for (int unsigned x = 0; x < o.px.size() && x < w.px.size(); x++) begin
                    if (o.px[x] == adapter.mask(w.px[x])) continue;
                    if (first < 0) first = x;
                    differ++;
                end
                if (owner.contract.pixel_check == A2C_VIDEO_PIX_EXACT && differ == 0 && o.px.size() > w.px.size()
                        && out.lines.size() < e.lines.size() && j + 1 < e.lines.size() && runs_on(o, w.px.size(), e.lines[j + 1])) begin
                    fail($sformatf("%s line %0d: no EOL on its last beat, so line %0d ran on into it with %0d of its %0d pixels",
                                   name, j, j + 1, o.px.size() - w.px.size(), e.lines[j + 1].px.size()));
                    j++;
                    // The lines pair again once the run-ons account for the
                    // missing lines, so their pixels are checked again.
                    run_ons++;
                    exact = out.lines.size() + run_ons == e.lines.size();
                end else if (o.px.size() != w.px.size()) begin
                    fail($sformatf("%s line %0d: %0d pixels, expected %0d%s", name, j, o.px.size(), w.px.size(),
                                   (owner.contract.pixel_check != A2C_VIDEO_PIX_EXACT) ? string'("") :
                                   (first >= 0) ? $sformatf("; first differing pixel x=%0d", first) : "; the pixels both hold agree"));
                end else if (exact && differ != 0) begin
                    fail($sformatf("%s line %0d: pixel x=%0d is 'h%0h, expected 'h%0h; %0d of %0d pixels differ", name, j,
                                   first, o.px[first], adapter.mask(w.px[first]), differ, w.px.size()));
                end
                if (!adapter.clocked && o.eol != e.lines[j].eol) begin
                    fail(o.eol ? $sformatf("%s line %0d: EOL on its last beat, where the expected frame has none", name, j)
                               : $sformatf("%s line %0d: no EOL on its last beat%s", name, j, sfx));
                end
            end
            if (!adapter.clocked && y < out.lines.size() && !out.lines[out.lines.size() - 1].eol) begin
                fail($sformatf("%s line %0d: no EOL on its last beat%s", name, out.lines.size() - 1, sfx));
            end
            if (adapter.has_eof && out.eof != e.eof) begin
                fail(out.eof ? $sformatf("%s: EOF on its last beat, where the expected frame has none", name)
                             : $sformatf("%s: no EOF on its last beat%s", name, sfx));
            end
            if (failures != errors) frames_bad++;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (!enabled) return;
            flush_strays();
            if (cur != null) close(0, {"the run ended before the frame did", a2c_run_ended_clause()});
            if (expected.size() != 0) begin
                fail($sformatf("%0d expected frames never came out, from %s%s", expected.size(), expected[0].label(),
                               a2c_run_ended_clause()));
            end
            if (unprinted != 0) begin
                `uvm_error("A2C_VIDEO", $sformatf("%s: %0d failures in all, %0d not printed", port_name, failures, unprinted))
            end
            `uvm_info("A2C_VIDEO", $sformatf("%s: %0d of %0d expected frames came out, from %0d planned, %0d lines, %0d beats; %0d frames failed, %0d failures",
                                             port_name, frames_out, expected_n, planned, lines_out, beats_out, frames_bad, failures), UVM_LOW)
        endfunction

        function int unsigned failures_seen();
            return failures;
        endfunction
    endclass : a2c_video_checker

    // Counts, per lane, the beats the plan puts on the clock after the beat
    // before on a handshaked input, and how many the driver offered so: with
    // valid high on every clock since the lane's previous transfer, read from
    // the monitor's flow counts. A sink that refuses a beat therefore does
    // not count against it. In Mode B the driver holds each beat until both
    // lanes took the one before, so a lane that trails gives the other idle
    // clocks the plan never asked for. A planned beat is found by the
    // monitor's own count, so items the test sends on the same agent around
    // or between the video runs move nothing.
    class a2c_video_lane_watch #(type ITEM = uvm_sequence_item) extends uvm_component;
        typedef a2c_video_lane_watch #(ITEM) this_t;

        uvm_analysis_imp_a2c_video_dut #(ITEM, this_t)   dut_export;
        uvm_analysis_imp_a2c_video_model #(ITEM, this_t) model_export;
        // Each lane's monitor; a lane whose monitor has no flow counts is not
        // watched.
        a2c_flow_counts                                  fc[2];
        bit                                              dual;

        // Per lane, the monitor's beat counts that are planned beats.
        protected bit              planned[2][int unsigned];
        protected int unsigned     beats[2];
        protected longint unsigned last_samples[2];
        protected longint unsigned last_valid[2];
        protected int unsigned     exact[2];

        `uvm_component_param_utils(a2c_video_lane_watch#(ITEM))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            dut_export   = new("dut_export", this);
            model_export = new("model_export", this);
        endfunction

        // The sequencer has granted a video beat. The driver asks for an item
        // only after every live lane took the one before, and the monitors
        // report a transfer before then, so the beat is the next each lane's
        // monitor reports, whatever the test sent before it.
        function void granted(bit zero_gap);
            if (!zero_gap) return;
            foreach (fc[l]) if (fc[l] != null) planned[l][beats[l]] = 1;
        endfunction

        protected function void beat(int lane);
            longint unsigned samples;
            longint unsigned valid;
            longint unsigned ready;
            longint unsigned transfers;
            if (fc[lane] == null) return;
            fc[lane].flow_counts(samples, valid, ready, transfers);
            if (planned[lane].exists(beats[lane]) && samples - last_samples[lane] == valid - last_valid[lane]) exact[lane]++;
            last_samples[lane] = samples;
            last_valid[lane]   = valid;
            beats[lane]++;
        endfunction

        virtual function void write_a2c_video_dut(ITEM t);
            beat(A2C_DUT_LANE);
        endfunction

        virtual function void write_a2c_video_model(ITEM t);
            beat(A2C_MODEL_LANE);
        endfunction

        function int unsigned planned_count();
            return planned[A2C_DUT_LANE].num();
        endfunction

        function int unsigned exact_count(a2c_lane_e lane);
            return exact[lane];
        endfunction
    endclass : a2c_video_lane_watch

    // An a2c_rt_checker unit rule that closes a unit at each frame's end, as
    // the adapter and the plan tell it: fv falling on a clocked stream; EOF
    // where the stream has it; and else the EOL that completes the lines of
    // the frame due, which a2c_video_test gives the rule through
    // frame_planned() before the frame's first beat, when the rule belongs
    // to an a2c_rt_checker connected to a video port's monitor. A frame due
    // that carries no EOF closes on its line count on a stream with EOF too,
    // so a cut frame stays one unit. A frame with no EOF that ends a line
    // when no frame is due raises one A2C_CFG.
    class a2c_video_unit_rule #(type ITEM = uvm_sequence_item) extends a2c_unit_rule #(ITEM) implements a2c_video_frame_listener;
        a2c_video_adapter #(ITEM) adapter;

        protected int unsigned due_lines[$];
        protected bit          due_eof[$];
        protected bit          prev_fv;
        protected int unsigned eols;
        protected bit          unplanned_reported;

        `uvm_object_param_utils(a2c_video_unit_rule#(ITEM))

        function new(string name = "a2c_video_unit_rule");
            super.new(name);
        endfunction

        virtual function void frame_planned(a2c_video_frame f);
            due_lines.push_back(f.lines.size());
            due_eof.push_back(f.eof);
        endfunction

        protected function bit frame_end();
            eols = 0;
            if (due_lines.size() != 0) begin
                void'(due_lines.pop_front());
                void'(due_eof.pop_front());
            end
            return 1;
        endfunction

        virtual function bit is_unit_end(ITEM t);
            bit fv;
            bit sof;
            bit eof;
            bit lv;
            bit eol;
            bit ended;
            adapter.get_frame(t, fv, sof, eof);
            adapter.get_line(t, lv, eol);
            if (adapter.clocked) begin
                ended   = prev_fv && !fv;
                prev_fv = fv;
                return ended;
            end
            if (sof) eols = 0;
            if (adapter.has_eof && eof) return frame_end();
            if (!eol) return 0;
            eols++;
            if (due_lines.size() == 0) begin
                if (!adapter.has_eof && !unplanned_reported) begin
                    unplanned_reported = 1;
                    `uvm_error("A2C_CFG", $sformatf("%s: a frame with no EOF ended a line while no planned frame gives its line count; a2c_video_test plans the frames of a video port, so connect the rule's a2c_rt_checker to that port's monitor",
                                                    get_name()))
                end
                return 0;
            end
            if (adapter.has_eof && due_eof[0]) return 0;
            if (eols < due_lines[0]) return 0;
            return frame_end();
        endfunction
    endclass : a2c_video_unit_rule

    // The a2c_flow_counts of a clocked video stream, whose monitor reports
    // every clock and counts nothing, so that a2c_rt_checker can take it as
    // an input: connect_in() this component. A pixel clock counts as an
    // offered beat and a transfer, and every clock as ready, since a clocked
    // stream cannot be refused. ap passes on every item.
    class a2c_video_flow_counts #(type ITEM = uvm_sequence_item) extends uvm_component implements a2c_flow_counts;
        typedef a2c_video_flow_counts #(ITEM) this_t;

        uvm_analysis_imp #(ITEM, this_t) analysis_export;
        uvm_analysis_port #(ITEM)        ap;
        a2c_video_adapter #(ITEM)        adapter;
        virtual a2c_clk_if               clk_vif;
        string                           port_name = "";

        protected longint unsigned n_samples;
        protected longint unsigned n_pixels;

        `uvm_component_param_utils(a2c_video_flow_counts#(ITEM))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            analysis_export = new("analysis_export", this);
            ap              = new("ap", this);
        endfunction

        virtual function void write(ITEM t);
            bit fv;
            bit sof;
            bit eof;
            bit lv;
            bit eol;
            adapter.get_frame(t, fv, sof, eof);
            adapter.get_line(t, lv, eol);
            n_samples++;
            n_pixels += fv && lv;
            ap.write(t);
        endfunction

        virtual function void flow_counts(output longint unsigned samples, output longint unsigned valid,
                                          output longint unsigned ready, output longint unsigned transfers);
            samples   = n_samples;
            valid     = n_pixels;
            ready     = n_samples;
            transfers = n_pixels;
        endfunction

        virtual function a2c_clk_vif_t flow_clock();
            return clk_vif;
        endfunction

        virtual function string flow_port();
            return port_name;
        endfunction
    endclass : a2c_video_flow_counts

    typedef class a2c_video_env;

    // The analysis port ap of the child component child of agent, if both
    // exist.
    class a2c_video_tap #(type ITEM = uvm_sequence_item);
        typedef uvm_port_component #(uvm_port_base #(uvm_tlm_if_base #(ITEM, ITEM))) port_t;

        static function uvm_port_base #(uvm_tlm_if_base #(ITEM, ITEM)) find(uvm_component agent, string child);
            uvm_component mon;
            port_t        pc;
            if (agent == null || !agent.has_child(child)) return null;
            mon = agent.get_child(child);
            if (!mon.has_child("ap") || !$cast(pc, mon.get_child("ap"))) return null;
            return pc.get_port();
        endfunction
    endclass : a2c_video_tap

    function automatic uvm_component a2c_video_child(uvm_component agent, string child);
        return (agent != null && agent.has_child(child)) ? agent.get_child(child) : null;
    endfunction

    // One video port of a video test. video_ports() declares it at build
    // with its adapter, and video_connect() gives it its agent at connect.
    virtual class a2c_video_port extends uvm_object;
        a2c_video_adapter_base   adapter_base;
        string                   port_name;
        uvm_component            agent;
        // The unit rules of the a2c_rt_checkers on this port's monitor.
        a2c_video_frame_listener listeners[$];

        function new(string name = "a2c_video_port");
            super.new(name);
        endfunction

        pure virtual function void build(a2c_video_env env);
        pure virtual function void connect(a2c_video_env env);

        // The agent's DUT-lane monitor, or null with an A2C_CFG error.
        function uvm_component monitor();
            uvm_component mon = a2c_video_child(agent, "mon");
            if (agent == null) begin
                `uvm_error("A2C_CFG", $sformatf("video port %s has no agent; connect it in video_connect()", port_name))
            end else if (mon == null) begin
                `uvm_error("A2C_CFG", $sformatf("video port %s: %s has no monitor mon", port_name, agent.get_full_name()))
            end
            return mon;
        endfunction

        // In Mode B, an A2C_CFG error when the agent has no model_mon.
        function bit has_model_mon(a2c_video_env env);
            if (a2c_video_child(agent, "model_mon") != null) return 1;
            `uvm_error("A2C_CFG", $sformatf("video port %s: both lanes run (a2c_dual_dut), but %s has no model-lane monitor model_mon, so the model lane goes unchecked",
                                            port_name, (agent == null) ? "the port" : agent.get_full_name()))
            return 0;
        endfunction

        function void add_listener(a2c_video_frame_listener l);
            foreach (listeners[i]) if (listeners[i] == l) return;
            listeners.push_back(l);
        endfunction
    endclass : a2c_video_port

    virtual class a2c_video_input_base extends a2c_video_port;
        function new(string name = "a2c_video_input_base");
            super.new(name);
        endfunction

        pure virtual task send(a2c_video_env env, a2c_video_cfg cfg, a2c_video_frame plan[$]);
        pure virtual function int unsigned idle_sent();
        // The planned back-to-back beats, and how many the driver offered so
        // on each lane; all 0 on a clocked input, where the driver times
        // every clock.
        pure virtual function void exactness(output int unsigned planned, output int unsigned dut, output int unsigned model,
                                             output bit dual);

        function void feed(a2c_video_frame f);
            foreach (listeners[i]) listeners[i].frame_planned(f);
        endfunction
    endclass : a2c_video_input_base

    // Holds the expected frames of one planned frame.
    class a2c_video_expected;
        a2c_video_frame frames[$];
    endclass : a2c_video_expected

    virtual class a2c_video_output_base extends a2c_video_port;
        a2c_txn_counter_base counter;
        a2c_video_contract   contract;

        protected a2c_video_expected cache[a2c_video_frame];

        function new(string name = "a2c_video_output_base");
            super.new(name);
        endfunction

        // The contract's frames for planned frame in, made on the first call.
        function void expected_for(a2c_video_frame in, output a2c_video_frame out[$]);
            if (!cache.exists(in)) begin
                a2c_video_expected x = new();
                contract.expected_frames(in, in.cfg, x.frames);
                if (x.frames.size() > 1) foreach (x.frames[k]) x.frames[k].part = k;
                cache[in] = x;
            end
            out = cache[in].frames;
        endfunction

        function int unsigned expected_beats(a2c_video_frame plan[$]);
            int unsigned n = 0;
            foreach (plan[f]) begin
                a2c_video_frame e[$];
                expected_for(plan[f], e);
                foreach (e[k]) n += e[k].beats(adapter_base.pixels_per_beat);
            end
            return n;
        endfunction

        function void feed(a2c_video_frame f);
            a2c_video_frame e[$];
            if (listeners.size() == 0) return;
            expected_for(f, e);
            foreach (e[k]) foreach (listeners[i]) listeners[i].frame_planned(e[k]);
        endfunction

        pure virtual function int unsigned failures();
    endclass : a2c_video_output_base

    // The video input: the input agent's sequencer and the port's adapter.
    // On a handshaked input it also watches the agent's mon and, in Mode B,
    // its model_mon.
    class a2c_video_input #(type ITEM = uvm_sequence_item) extends a2c_video_input_base;
        typedef a2c_video_input #(ITEM) this_t;

        uvm_sequencer_base           sqr;
        a2c_video_adapter #(ITEM)    adapter;
        a2c_video_seq #(ITEM)        seq;
        a2c_video_lane_watch #(ITEM) watch;

        // The idle clocks of the sequences before seq.
        protected int unsigned idle_before;

        `uvm_object_param_utils(a2c_video_input#(ITEM))

        function new(string name = "a2c_video_input");
            super.new(name);
        endfunction

        static function this_t make(string port_name, a2c_video_adapter #(ITEM) adapter);
            this_t p;
            if (adapter == null) begin
                `uvm_fatal("A2C_CFG", $sformatf("a2c_video_input::make('%s') was given no adapter; create the port's adapter in video_ports()",
                                                port_name))
            end
            p = new(port_name);
            p.port_name    = port_name;
            p.adapter      = adapter;
            p.adapter_base = adapter;
            return p;
        endfunction

        virtual function void build(a2c_video_env env);
            if (adapter.clocked) return;
            watch = a2c_video_lane_watch#(ITEM)::type_id::create({port_name, "_watch"}, env);
            watch.dual = env.dual;
        endfunction

        virtual function void connect(a2c_video_env env);
            uvm_port_base #(uvm_tlm_if_base #(ITEM, ITEM)) mon;
            uvm_port_base #(uvm_tlm_if_base #(ITEM, ITEM)) model_mon;
            if (!$cast(sqr, a2c_video_child(agent, "sqr")) || sqr == null) begin
                `uvm_error("A2C_CFG", $sformatf("video input %s: %s has no sequencer sqr; connect the input agent in video_connect()",
                                                port_name, (agent == null) ? "no agent" : agent.get_full_name()))
            end
            if (watch == null) return;
            mon = a2c_video_tap#(ITEM)::find(agent, "mon");
            if (mon == null) return;
            mon.connect(watch.dut_export);
            void'($cast(watch.fc[A2C_DUT_LANE], monitor()));
            if (!env.dual || !has_model_mon(env)) return;
            model_mon = a2c_video_tap#(ITEM)::find(agent, "model_mon");
            if (model_mon != null) model_mon.connect(watch.model_export);
            void'($cast(watch.fc[A2C_MODEL_LANE], a2c_video_child(agent, "model_mon")));
        endfunction

        virtual task send(a2c_video_env env, a2c_video_cfg cfg, a2c_video_frame plan[$]);
            if (sqr == null) return;
            if (seq != null) idle_before += seq.idle_sent;
            seq = a2c_video_seq#(ITEM)::type_id::create({port_name, "_seq"});
            seq.cfg     = cfg;
            seq.adapter = adapter;
            seq.plan_ap = env.plan_ap;
            seq.plan    = plan;
            seq.watch   = watch;
            seq.start(sqr);
        endtask

        virtual function int unsigned idle_sent();
            return idle_before + ((seq == null) ? 0 : seq.idle_sent);
        endfunction

        virtual function void exactness(output int unsigned planned, output int unsigned dut, output int unsigned model,
                                        output bit dual);
            planned = (watch == null) ? 0 : watch.planned_count();
            dut     = (watch == null) ? 0 : watch.exact_count(A2C_DUT_LANE);
            model   = (watch == null) ? 0 : watch.exact_count(A2C_MODEL_LANE);
            dual    = watch != null && watch.dual;
        endfunction
    endclass : a2c_video_input

    // One checked video output: the port's adapter, and optionally a
    // contract other than the default; video_connect() gives it its agent
    // and optionally its a2c_txn_counter, which the video test declares the
    // contract's beats to. In Mode B (a2c_dual_dut) a second checker judges
    // the agent's model_mon.
    class a2c_video_output #(type ITEM = uvm_sequence_item) extends a2c_video_output_base;
        typedef a2c_video_output #(ITEM) this_t;

        a2c_video_adapter #(ITEM) adapter;
        a2c_video_checker #(ITEM) checkers[$];

        `uvm_object_param_utils(a2c_video_output#(ITEM))

        function new(string name = "a2c_video_output");
            super.new(name);
        endfunction

        static function this_t make(string port_name, a2c_video_adapter #(ITEM) adapter, a2c_video_contract contract = null);
            this_t p;
            if (adapter == null) begin
                `uvm_fatal("A2C_CFG", $sformatf("a2c_video_output::make('%s') was given no adapter; create the port's adapter in video_ports()",
                                                port_name))
            end
            p = new(port_name);
            p.port_name    = port_name;
            p.adapter      = adapter;
            p.adapter_base = adapter;
            p.contract     = (contract != null) ? contract : a2c_video_contract::type_id::create({port_name, "_contract"});
            return p;
        endfunction

        protected function a2c_video_checker #(ITEM) new_checker(a2c_video_env env, string suffix, string lane);
            a2c_video_checker #(ITEM) c = a2c_video_checker#(ITEM)::type_id::create({port_name, suffix}, env);
            c.adapter   = adapter;
            c.owner     = this;
            c.port_name = {port_name, lane};
            return c;
        endfunction

        virtual function void build(a2c_video_env env);
            checkers.push_back(new_checker(env, "_checker", env.dual ? " DUT lane" : ""));
            if (env.dual) checkers.push_back(new_checker(env, "_model_checker", " model lane"));
        endfunction

        virtual function void connect(a2c_video_env env);
            uvm_port_base #(uvm_tlm_if_base #(ITEM, ITEM)) mon = a2c_video_tap#(ITEM)::find(agent, "mon");
            uvm_port_base #(uvm_tlm_if_base #(ITEM, ITEM)) model_mon;
            foreach (checkers[i]) env.plan_ap.connect(checkers[i].plan_export);
            if (monitor() == null || mon == null) begin
                foreach (checkers[i]) checkers[i].enabled = 0;
                return;
            end
            mon.connect(checkers[0].analysis_export);
            if (!env.dual) return;
            model_mon = a2c_video_tap#(ITEM)::find(agent, "model_mon");
            if (has_model_mon(env) && model_mon != null) model_mon.connect(checkers[1].analysis_export);
            else checkers[1].enabled = 0;
        endfunction

        virtual function int unsigned failures();
            int unsigned n = 0;
            foreach (checkers[i]) n += checkers[i].failures_seen();
            return n;
        endfunction
    endclass : a2c_video_output

    // What a2c_video_env asks of the video test that builds it.
    interface class a2c_video_hooks;
        pure virtual function void video_ports();
        pure virtual function void video_connect();
        pure virtual function void configure_video(a2c_video_cfg cfg);
        pure virtual function void edit_plan(a2c_video_cfg cfg, ref a2c_video_frame plan[$]);
    endclass

    // The video side of a video test, a child of the test named video. Its
    // build_phase calls the test's video_ports(), which declares each port
    // with its adapter and reads nothing the test's env builds, and creates
    // the checkers; its connect_phase calls video_connect(), which gives each
    // port its agent, and connects them. So nothing depends on the order in
    // which the test's children build.
    class a2c_video_env extends uvm_env;
        // The test's configuration, which corner tests and plusargs set.
        a2c_video_cfg                        cfg;
        a2c_video_hooks                      hooks;
        string                               corner = "";
        a2c_video_input_base                 in;
        a2c_video_output_base                outs[$];
        uvm_analysis_port #(a2c_video_frame) plan_ap;
        // Mode B, from a2c_dual_dut.
        bit                                  dual;
        // Every frame planned so far, over all runs.
        a2c_video_frame                      plan[$];
        bit                                  valid;

        protected bit contract_logged;

        `uvm_component_utils(a2c_video_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function void add_input(a2c_video_input_base p);
            if (in != null) `uvm_fatal("A2C_CFG", "video_ports() added a second video input; a video test drives one")
            in = p;
        endfunction

        function void add_output(a2c_video_output_base p);
            outs.push_back(p);
        endfunction

        function a2c_video_output_base output_port(string port_name);
            foreach (outs[i]) if (outs[i].port_name == port_name) return outs[i];
            `uvm_error("A2C_CFG", $sformatf("video_connect() named output %s, which video_ports() did not add", port_name))
            return null;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            plan_ap = new("plan_ap", this);
            cfg     = a2c_video_cfg::type_id::create("cfg");
            void'(uvm_config_db#(bit)::get(this, "", "a2c_dual_dut", dual));
            if (hooks == null) `uvm_fatal("A2C_CFG", "a2c_video_env has no hooks; a2c_video_test builds it")
            hooks.video_ports();
            if (in == null) `uvm_fatal("A2C_CFG", "video_ports() added no video input; call add_video_input() with a2c_video_input::make()")
            cfg.from_adapter(in.adapter_base);
            hooks.configure_video(cfg);
            if (corner != "") cfg.apply_corner(corner);
            cfg.apply_plusargs();
            in.build(this);
            foreach (outs[i]) outs[i].build(this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            hooks.video_connect();
            in.connect(this);
            foreach (outs[i]) outs[i].connect(this);
        endfunction

        virtual function void end_of_elaboration_phase(uvm_phase phase);
            super.end_of_elaboration_phase(phase);
            valid = cfg.validate();
        endfunction

        // Once every component has connected: each a2c_rt_checker on a video
        // port's DUT-lane monitor gets that port's planned frames for its
        // a2c_video_unit_rule, and one whose output's contract does not keep
        // frames one for one is turned off.
        virtual function void start_of_simulation_phase(uvm_phase phase);
            a2c_rt_checker_base      rts[$];
            a2c_video_frame_listener l;
            super.start_of_simulation_phase(phase);
            a2c_rt_checker_base::get_checkers(rts);
            foreach (rts[k]) begin
                uvm_component inc = rts[k].in_component();
                uvm_component outc = rts[k].out_component();
                if (inc != null && inc == a2c_video_child(in.agent, "mon") && rts[k].in_unit_rule() != null
                        && $cast(l, rts[k].in_unit_rule())) in.add_listener(l);
                foreach (outs[i]) begin
                    if (outc == null || outc != a2c_video_child(outs[i].agent, "mon")) continue;
                    if (rts[k].out_unit_rule() != null && $cast(l, rts[k].out_unit_rule())) outs[i].add_listener(l);
                    if (outs[i].contract.preserves_frames()) continue;
                    rts[k].turn_off();
                    `uvm_info("A2C_VIDEO", $sformatf("%s on %s does not keep frames one for one, so %s is off",
                                                     outs[i].contract.get_type_name(), outs[i].port_name, rts[k].get_full_name()), UVM_LOW)
                end
            end
        endfunction

        // Sends the frames of c on the input after planning them and letting
        // the test edit the plan, declaring each counted output's beats,
        // giving the unit rules their frames and, on the first run, logging
        // the contract each output checks. A frame the test added with no
        // cfg gets c.
        // The test's cfg was validated at end of elaboration; another gets
        // the plusargs and is validated here.
        task send_frames(a2c_video_cfg c);
            a2c_video_frame p[$];
            if (c != cfg) c.apply_plusargs();
            if (c == cfg ? !valid : !c.validate()) begin
                `uvm_info("A2C_VIDEO", "the video configuration broke a rule (A2C_CFG above), so no frame is sent", UVM_LOW)
                return;
            end
            c.make_plan(p);
            hooks.edit_plan(c, p);
            if (p.size() == 0) begin
                `uvm_fatal("A2C_CFG", "edit_plan() left the run with no frame; a test that sends no frame does not call send_video()")
                return;
            end
            foreach (p[f]) if (p[f].cfg == null) p[f].cfg = c;
            c.mark_zero_gaps(p);
            `uvm_info("A2C_VIDEO", $sformatf("corner %s; %s", (c.corner == "") ? "none" : c.corner, c.describe()), UVM_LOW)
            foreach (outs[i]) begin
                if (!contract_logged) begin
                    `uvm_info("A2C_VIDEO", $sformatf("output %s checks the contract %s", outs[i].port_name, outs[i].contract.describe()),
                              UVM_LOW)
                end
                if (outs[i].counter != null && !outs[i].adapter_base.clocked) outs[i].counter.expect_count(outs[i].expected_beats(p));
            end
            contract_logged = 1;
            foreach (p[f]) begin
                plan.push_back(p[f]);
                in.feed(p[f]);
                foreach (outs[i]) outs[i].feed(p[f]);
            end
            in.send(this, c, p);
        endtask

        // A configuration of the input's stream kind and pixel shape, with
        // the class defaults, for a test that sends runs of its own.
        function a2c_video_cfg new_cfg(string name = "cfg");
            a2c_video_cfg c = a2c_video_cfg::type_id::create(name);
            c.from_adapter(in.adapter_base);
            return c;
        endfunction

        function int unsigned idle_sent();
            return (in == null) ? 0 : in.idle_sent();
        endfunction

        // A zero-gap corner is exact on a lane only while the other lane keeps
        // up, so in Mode B a corner test warns when its corner did not reach
        // the DUT lane as planned.
        virtual function void report_phase(uvm_phase phase);
            int unsigned planned;
            int unsigned dut;
            int unsigned model;
            bit          two;
            super.report_phase(phase);
            if (in == null || !valid) return;
            in.exactness(planned, dut, model, two);
            if (planned == 0) return;
            `uvm_info("A2C_VIDEO", $sformatf("%0d planned back-to-back beats were offered back to back on the DUT lane%s, of %0d",
                                             dut, two ? $sformatf(" and %0d on the model lane", model) : "", planned), UVM_LOW)
            if (two && corner inside {"no_blank", "back_to_back"} && dut < planned) begin
                `uvm_warning("A2C_VIDEO", $sformatf("corner %s: %0d of %0d planned back-to-back beats reached the DUT lane as planned; in Mode B the driver holds each beat until both lanes took the one before, so a trailing lane adds idle clocks",
                                                    corner, dut, planned))
            end
        endfunction
    endclass : a2c_video_env

    // A video test of a block. BASE is the block's generated <block>_base_test,
    // or a class that extends it; this class adds a2c_video_env, runs the
    // video stimulus as run_body(), and adds the handshaked blanking to
    // stimulus_sent(), so the derived run timeout follows the blanking. The
    // bench extends it once, as <block>_video_test, with video_ports(),
    // video_connect(), configure_dut() and, where it needs one,
    // edit_plan(), and `a2c_video_corner_tests(<block>_video_test) adds a
    // test per corner.
    virtual class a2c_video_test #(type BASE = uvm_test) extends BASE implements a2c_video_hooks;
        // Set by a corner test's constructor.
        string        corner = "";
        a2c_video_env video;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // Build: calls add_video_input() once, with a2c_video_input::make()
        // and the port's adapter, and add_video_output() for each checked
        // output. It must not read the env, which may not be built yet.
        pure virtual function void video_ports();

        // Connect: names each port's agent, with connect_video_input() and
        // connect_video_output().
        pure virtual function void video_connect();

        // Sets the geometry and knobs before the corner and the plusargs.
        virtual function void configure_video(a2c_video_cfg cfg);
        endfunction

        // Programs the DUT for cfg before the first frame.
        virtual task configure_dut(a2c_video_cfg cfg);
        endtask

        // Edits the plan of each run send_video() sends, for stimulus the
        // cfg cannot describe, such as pixel values the test computes. It
        // may change, drop or add frames, and runs before the contract sees
        // them and before any beat is declared or sent, so both follow the
        // edits. A frame added with no cfg gets the run's; a plan left empty
        // is an A2C_CFG fatal. cfg is the run's, which tells a test's runs
        // apart.
        virtual function void edit_plan(a2c_video_cfg cfg, ref a2c_video_frame plan[$]);
        endfunction

        function void add_video_input(a2c_video_input_base p);
            video.add_input(p);
        endfunction

        function void add_video_output(a2c_video_output_base p);
            video.add_output(p);
        endfunction

        // agent is the input port's agent, whose sqr the frames go to.
        function void connect_video_input(uvm_component agent);
            video.in.agent = agent;
        endfunction

        // agent is the output port's agent, whose mon, and model_mon in Mode
        // B, the checkers read; counter, if any, gets the contract's beats.
        function void connect_video_output(string port_name, uvm_component agent, a2c_txn_counter_base counter = null);
            a2c_video_output_base p = video.output_port(port_name);
            if (p == null) return;
            p.agent   = agent;
            p.counter = counter;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            video        = a2c_video_env::type_id::create("video", this);
            video.hooks  = this;
            video.corner = corner;
        endfunction

        // Sends cfg's frames, or the test's when cfg is null. A test that
        // overrides run_body() may send several runs, each from
        // new_video_cfg(), with register writes between them.
        task send_video(a2c_video_cfg cfg = null);
            video.send_frames((cfg == null) ? video.cfg : cfg);
        endtask

        function a2c_video_cfg new_video_cfg(string name = "cfg");
            return video.new_cfg(name);
        endfunction

        virtual task run_body();
            if (video.valid) configure_dut(video.cfg);
            send_video();
        endtask

        virtual function int unsigned stimulus_sent();
            return super.stimulus_sent() + video.idle_sent();
        endfunction
    endclass : a2c_video_test

endpackage : a2c_video_pkg

`endif // A2C_VIDEO_PKG_SV
