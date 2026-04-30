
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
// GENERATED_CODE_PARAM --context=ip.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package ip_package;
localparam int unsigned IP_DATA_WIDTH = 32'h0000_0008;  // Per-instance data width
localparam int unsigned IP_MEM_DEPTH = 32'h0000_0010;  // Per-instance memory depth

// types
typedef logic[IP_DATA_WIDTH-1:0] ipDataT; //IP data word, parameterizable
typedef logic[1-1:0] enableT; //Single enable bit
typedef logic[$clog2(IP_MEM_DEPTH)-1:0] ipMemAddrT; //Index into ipMem (0 .. IP_MEM_DEPTH-1)

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

endpackage : ip_package
// GENERATED_CODE_END
