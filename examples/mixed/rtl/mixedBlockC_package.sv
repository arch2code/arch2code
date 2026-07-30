
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=mixed --context=mixedBlockC.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package mixed_mixedBlockC_package;
localparam int unsigned CSIZE = 32'h0000_0002;  // The size of C
localparam int unsigned CSIZE_PLUS = 32'h0000_0003;  // The size of C plus 1

// types
typedef logic[CSIZE-1:0] cSizeT; //size of c
typedef logic[CSIZE_PLUS-1:0] cSizePlusT; //size of c plus 1
typedef logic[13-1:0] cBiggerT; //yet another type

// enums

// structures
typedef struct packed {
    cSizeT variablec; //Two bits of C
    cSizePlusT variablec2; //Three bits of C
} seeSt;

typedef struct packed {
    cBiggerT hdr; //
} cHeaderSt;

endpackage : mixed_mixedBlockC_package
// GENERATED_CODE_END
