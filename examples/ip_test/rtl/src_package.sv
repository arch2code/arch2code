
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --context=src.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package src_package;
localparam int unsigned OUT0_DATA_WIDTH = 32'h0000_0008;  // Width fed to uIp0
localparam int unsigned OUT1_DATA_WIDTH = 32'h0000_0046;  // Width fed to uIp1

// types
typedef logic[OUT0_DATA_WIDTH-1:0] srcOut0DataT; //src out0 data word, parameterizable
typedef logic[OUT1_DATA_WIDTH-1:0] srcOut1DataT; //src out1 data word, parameterizable
typedef logic[1-1:0] srcMarkerT; //src high-word marker bit

// enums

// structures
typedef struct packed {
    srcMarkerT marker; //marker bit copied through the thunker
    srcOut0DataT data; //src out0 payload
} srcOut0St;

typedef struct packed {
    srcMarkerT marker; //marker bit above bit 64 for the 70-bit variant
    srcOut1DataT data; //src out1 payload
} srcOut1St;

endpackage : src_package
// GENERATED_CODE_END
