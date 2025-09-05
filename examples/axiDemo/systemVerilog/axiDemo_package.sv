
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
// GENERATED_CODE_PARAM --context=axiDemo.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package axiDemo_package;
// Generated Import package statement(s)
import axiStd_package::*;
localparam int AXI_ADDRESS_WIDTH = 32'h0000_0020;  // The width of the AXI address busses
localparam int AXI_DATA_WIDTH = 32'h0000_0020;  // The width of the AXI data busses
localparam int AXI_STROBE_WIDTH = 32'h0000_0004;  // The width of the AXI strobe signals

// types
typedef logic[32-1:0] axiAddrT; //Address Width sizing from constant AXI_ADDRESS_WIDTH
typedef logic[32-1:0] axiDataT; //Width of the data bus. sizing from constant AXI_DATA_WIDTH
typedef logic[4-1:0] axiStrobeT; //Width of the strobe bus. sizing from constant AXI_STROBE_WIDTH

// enums

// structures
typedef struct packed {
    axiAddrT addr; //
} axiAddrSt;

typedef struct packed {
    axiDataT data; //
} axiDataSt;

typedef struct packed {
    axiStrobeT strobe; //
} axiStrobeSt;

endpackage : axiDemo_package
// GENERATED_CODE_END
