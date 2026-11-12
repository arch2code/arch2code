
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=uvmVideo --context=../../yaml/uvmVideo.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package uvmVideo_package;
localparam int unsigned UVM_VIDEO_PIXELS = 32'h0000_0002;  // Pixels per beat
localparam int unsigned UVM_VIDEO_WIDTH = 32'h0000_0010;  // Pixels per line uSrc sends in the SystemC testbench
localparam int unsigned UVM_VIDEO_HEIGHT = 32'h0000_0004;  // Lines per frame uSrc sends in the SystemC testbench
localparam int unsigned UVM_VIDEO_FRAMES = 32'h0000_0003;  // Frames uSrc sends in the SystemC testbench

// types
typedef logic[8-1:0] uvmVideoPixelT; //One pixel
typedef logic[1-1:0] uvmVideoBitT; //A level or marker

// enums

// structures
typedef struct packed {
    uvmVideoBitT fv; //Frame valid
    uvmVideoBitT lv; //Line valid
    uvmVideoPixelT [UVM_VIDEO_PIXELS-1:0] pixels; //
} uvmVideoRawSt;

typedef struct packed {
    uvmVideoPixelT [UVM_VIDEO_PIXELS-1:0] pixels; //
} uvmVideoBeatSt;

typedef struct packed {
    uvmVideoBitT id; //
} uvmVideoIdSt;

typedef struct packed {
    uvmVideoBitT sof; //Start of frame
} uvmVideoUserSt;

endpackage : uvmVideo_package
// GENERATED_CODE_END
