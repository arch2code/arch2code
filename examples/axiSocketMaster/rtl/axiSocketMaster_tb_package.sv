
// 
// GENERATED_CODE_PARAM --project=axiSocketMaster --context=axiSocketMaster_tb.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package axiSocketMaster_tb_package;
// Generated Import package statement(s)
import axiSocketMaster_axiStd_package::*;
localparam int unsigned AXI_ADDRESS_WIDTH = 32'h0000_0020;  // The width of the AXI address busses
localparam int unsigned AXI_DATA_WIDTH = 32'h0000_0020;  // The width of the AXI data busses
localparam int unsigned AXI_STROBE_WIDTH = 32'h0000_0004;  // The width of the AXI strobe signals

// types
typedef logic[AXI_ADDRESS_WIDTH-1:0] axiAddrT; //Address Width
typedef logic[AXI_DATA_WIDTH-1:0] axiDataT; //Width of the data bus.
typedef logic[AXI_STROBE_WIDTH-1:0] axiStrobeT; //Width of the strobe bus.

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

endpackage : axiSocketMaster_tb_package
// GENERATED_CODE_END
