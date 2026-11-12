`ifndef A2C_VIDEO_MACROS_SVH
`define A2C_VIDEO_MACROS_SVH

// A bench includes this file, as it includes uvm_macros.svh, in the package
// that defines its video test: `include "uvm/a2c_video_macros.svh", which
// a2c.f's include directory reaches.
//
// `a2c_video_corner_tests(T) defines, for a video test class T, one test per
// corner, T_<corner>, that sets the corner and nothing else. Every corner is
// defined; a regression lists the ones the bench's stream allows, and a
// corner its input adapter cannot carry stops at end of elaboration with
// one A2C_CFG fatal naming it.
`define a2c_video_corner_test(T, C) \
    class T``_``C extends T; \
        `uvm_component_utils(T``_``C) \
        function new(string name, uvm_component parent); \
            super.new(name, parent); \
            corner = `"C`"; \
        endfunction \
    endclass : T``_``C

`define a2c_video_corner_tests(T) \
    `a2c_video_corner_test(T, blanking) \
    `a2c_video_corner_test(T, no_blank) \
    `a2c_video_corner_test(T, back_to_back) \
    `a2c_video_corner_test(T, short_line) \
    `a2c_video_corner_test(T, long_line) \
    `a2c_video_corner_test(T, cut_frame) \
    `a2c_video_corner_test(T, cut_lv_high) \
    `a2c_video_corner_test(T, fv_rise_line) \
    `a2c_video_corner_test(T, lv_vblank) \
    `a2c_video_corner_test(T, random)

`endif // A2C_VIDEO_MACROS_SVH
