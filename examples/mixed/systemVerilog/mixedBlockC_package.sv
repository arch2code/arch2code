// GENERATED_CODE_PARAM --context mixedBlockC.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package mixedBlockC_package;
//         CSIZE =                              'd2;  // The size of C
localparam CSIZE =                            32'h0000_0002;  // The size of C
//         CSIZE_PLUS =                         'd3;  // The size of C plus 1
localparam CSIZE_PLUS =                       32'h0000_0003;  // The size of C plus 1

// types
typedef logic[2-1:0] cSizeT; //size of c sizing from constant CSIZE
typedef logic[3-1:0] cSizePlusT; //size of c plus 1 sizing from constant CSIZE_PLUS
typedef logic[13-1:0] cBiggerT; //yet another type

// enums

// structures
typedef struct packed {
    cSizeT variablec; //
    cSizePlusT variablec2; //
} seeSt;

typedef struct packed {
    cBiggerT hdr; //
} cHeaderSt;

endpackage : mixedBlockC_package
// GENERATED_CODE_END
