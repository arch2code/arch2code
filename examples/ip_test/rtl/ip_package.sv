
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
// GENERATED_CODE_PARAM --context=ip.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package ip_package;
localparam int unsigned IP_DATA_WIDTH = 32'h0000_0008;  // Per-instance data width
localparam int unsigned IP_MEM_DEPTH = 32'h0000_0010;  // Per-instance memory depth
localparam int unsigned IP_DATA_WIDTH_X2 = 32'h0000_0010;  // Derived width, 2x data (maxValue auto-derived)

// types
typedef logic[IP_DATA_WIDTH-1:0] ipDataT; //IP data word, parameterizable
typedef logic[1-1:0] enableT; //Single enable bit
typedef logic[$clog2(IP_MEM_DEPTH)-1:0] ipMemAddrT; //Index into ipMem (0 .. IP_MEM_DEPTH-1)
typedef logic[8-1:0] ipFixedT; //Fixed 8-bit byte (non-parameterizable)
typedef logic[8-1:0] ipFixedAddrT; //Fixed 8-bit address index (non-parameterizable)

// enums
typedef enum logic[2-1:0] {              //IP operating mode
    IP_MODE_OFF = 0,         // Off
    IP_MODE_LOW = 1,         // Low power
    IP_MODE_HIGH = 2        // High performance
} ipModeT;

// structures
typedef struct packed {
    ipDataT data; //Data word
} ipDataSt;

typedef struct packed {
    enableT enable; //Enable bit
    ipModeT mode; //Operating mode
    ipDataT threshold; //Threshold value
} ipCfgSt;

typedef struct packed {
    ipDataT data; //Data word
} ipMemSt;

typedef struct packed {
    ipMemAddrT address; //Memory address
} ipMemAddrSt;

typedef struct packed {
    ipDataT [IP_MEM_DEPTH-1:0] samples; //Burst of parameterizable samples
} ipBurstSt;

typedef struct packed {
    ipFixedT b; //Fixed byte
} ipFixedSt;

typedef struct packed {
    ipFixedAddrT a; //Fixed-width address
} ipFixedAddrSt;

endpackage : ip_package
// GENERATED_CODE_END
