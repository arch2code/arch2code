
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
// GENERATED_CODE_PARAM --contexts=axiDemo.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package axiDemo_package;
// Generated Import package statement(s)
import axiStd_package::*;
//constants as defined by the scope of the following context(s): ('axiDemo.yaml',)
//         AXI_ADDRESS_WIDTH =                 'd32;  // The width of the AXI address busses
localparam AXI_ADDRESS_WIDTH =               32'h0000_0020;  // The width of the AXI address busses
//         AXI_DATA_WIDTH =                    'd32;  // The width of the AXI data busses
localparam AXI_DATA_WIDTH =                  32'h0000_0020;  // The width of the AXI data busses
//         AXI_STROBE_WIDTH =                   'd4;  // The width of the AXI strobe signals
localparam AXI_STROBE_WIDTH =                 32'h0000_0004;  // The width of the AXI strobe signals

// types
typedef logic[32-1:0] axiAddrT; //Address Width sizing from constant AXI_ADDRESS_WIDTH
typedef logic[32-1:0] axiDataT; //Width of the data bus. sizing from constant AXI_DATA_WIDTH
typedef logic[4-1:0] axiStrobeT; //Width of the strobe bus. sizing from constant AXI_STROBE_WIDTH

// enums
typedef enum logic[1-1:0] {          //Generated type for addressing top instances
    ADDR_ID_TOP_UCONSUMER = 0 // uConsumer instance address
} addr_id_top;

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
