
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --context=ip.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package ip_package;
localparam int unsigned IP_DATA_WIDTH = 32'h0000_0008;  // Per-instance data width
localparam int unsigned IP_MEM_DEPTH = 32'h0000_0010;  // Per-instance memory depth
localparam int unsigned IP_DATA_WIDTH_X2 = 32'h0000_0010;  // Derived width, 2x data (maxValue auto-derived)
localparam int unsigned IP_FIXED_NIBBLE_COUNT = 32'h0000_0005;  // Fixed array length for non-parameterized type tests
localparam int unsigned IP_FIXED_PAIR_COUNT = 32'h0000_0002;  // Fixed nested-structure array length
localparam int unsigned IP_FIXED_WORD_COUNT = 32'h0000_0006;  // Derived fixed array length
localparam int unsigned IP_FIXED_DEPTH = 32'h0000_0009;  // Fixed depth for widthLog2 and widthLog2minus1 tests

// types
typedef logic[IP_DATA_WIDTH-1:0] ipDataT; //IP data word, parameterizable
typedef logic[1-1:0] enableT; //Single enable bit
typedef logic[$clog2(IP_MEM_DEPTH)-1:0] ipMemAddrT; //Index into ipMem (0 .. IP_MEM_DEPTH-1)
typedef logic[8-1:0] ipFixedT; //Fixed 8-bit byte (non-parameterizable)
typedef logic[8-1:0] ipFixedAddrT; //Fixed 8-bit address index (non-parameterizable)
typedef logic[4-1:0] ipNibbleT; //Fixed unsigned nibble
typedef logic signed[4-1:0] ipSignedNibbleT; //Fixed signed nibble
typedef logic signed[3-1:0] ipSigned3T; //Fixed signed 3-bit value
typedef logic[5-1:0] ipUnsigned5T; //Fixed unsigned 5-bit value
typedef logic[9-1:0] ipUnsigned9T; //Fixed unsigned 9-bit value
typedef logic[16-1:0] ipWordT; //Fixed 16-bit word
typedef logic[37-1:0] ipWide37T; //Fixed 37-bit value crossing a 32-bit boundary
typedef logic[$clog2(IP_FIXED_DEPTH+1)-1:0] ipFixedCountT; //Fixed count field wide enough for 0..IP_FIXED_DEPTH
typedef logic[$clog2(IP_FIXED_DEPTH)-1:0] ipFixedIndexT; //Fixed index field wide enough for 0..IP_FIXED_DEPTH-1

// enums
typedef enum logic[2-1:0] {              //IP operating mode
    IP_MODE_OFF = 0,         // Off
    IP_MODE_LOW = 1,         // Low power
    IP_MODE_HIGH = 2        // High performance
} ipModeT;
typedef enum logic[3-1:0] {       //Fixed status enum
    IP_STATUS_IDLE = 0,      // Idle
    IP_STATUS_BUSY = 1,      // Busy
    IP_STATUS_DONE = 4      // Done
} ipFixedStatusT;
typedef enum logic[8-1:0] {       //Fixed-width opcode enum
    IP_OP_NOP = 0,           // No operation
    IP_OP_LOAD = 3,          // Load
    IP_OP_STORE = 9         // Store
} ipFixedOpcodeT;

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

typedef struct packed {
    ipFixedOpcodeT opcode; //Fixed opcode
    ipFixedStatusT status; //Fixed status
    ipNibbleT tag; //Fixed packet tag
} ipFixedHeaderSt;

typedef struct packed {
    ipSigned3T tiny; //Signed 3-bit field
    ipSignedNibbleT offset; //Signed 4-bit field
    ipUnsigned5T magnitude; //Unsigned 5-bit field
    ipUnsigned9T lane; //Unsigned 9-bit field
} ipFixedSignedSt;

typedef struct packed {
    ipNibbleT [IP_FIXED_NIBBLE_COUNT-1:0] nibbles; //Fixed nibble array
    ipWordT [IP_FIXED_PAIR_COUNT-1:0] words; //Fixed word array
} ipFixedArraySt;

typedef struct packed {
    ipFixedCountT count; //Fixed widthLog2 count
    ipFixedIndexT index; //Fixed widthLog2minus1 index
} ipFixedLog2St;

typedef struct packed {
    ipFixedHeaderSt header; //Nested fixed header
    ipFixedSignedSt signedFields; //Nested signed and narrow fields
    ipFixedArraySt [IP_FIXED_PAIR_COUNT-1:0] arrays; //Nested fixed arrays
    ipFixedLog2St log2Fields; //Nested fixed log2 fields
    ipWide37T wideValue; //Wide fixed value
} ipFixedNestedSt;

endpackage : ip_package
// GENERATED_CODE_END
