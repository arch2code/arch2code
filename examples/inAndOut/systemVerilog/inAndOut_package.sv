
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
// GENERATED_CODE_PARAM --context=inAndOut.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package inAndOut_package;
//         ASIZE =                              'd1;  // The size of A
localparam ASIZE =                            32'h0000_0001;  // The size of A
//         ASIZE2 =                             'd2;  // The size of A+1
localparam ASIZE2 =                           32'h0000_0002;  // The size of A+1
//         BIGE33 =                    'd8589934591;  // Test constant for numbers slightly bigger than 32 bits
localparam BIGE33 =                  64'h0000_0001_FFFF_FFFF;  // Test constant for numbers slightly bigger than 32 bits
//         BIGE53 =             'd18014398509481983;  // Test constant for numbers slightly bigger than 32 bits
localparam BIGE53 =           64'h003F_FFFF_FFFF_FFFF;  // Test constant for numbers slightly bigger than 32 bits

// types
typedef logic[2-1:0] twoBitT; //this is a 2 bit type
typedef logic[3-1:0] threeBitT; //this is a 3 bit type
typedef logic[4-1:0] fourBitT; //this is a 4 bit type
typedef logic[1-1:0] aSizeT; //type of width ASIZE sizing from constant ASIZE
typedef logic[2-1:0] aBiggerT; //yet another type sizing from constant ASIZE2
typedef logic[5-1:0] bSizeT; //for addressing memory, temp, unused

// enums
typedef enum logic[1-1:0] {               //either ready or not ready
    READY_NO = 0,            // Not ready
    READY_YES = 1           // Ready
} readyT;
typedef enum logic[1-1:0] {          //Generated type for addressing inAndOut instances
    ADDR_ID_TOP_UINANDOUT0 = 0, // uInAndOut0 instance address
    ADDR_ID_TOP_UINANDOUT1 = 1 // uInAndOut1 instance address
} addr_id_top;

// structures
typedef struct packed {
    aSizeT [ASIZE2-1:0] variablea; //One bit of A
} aSt;

typedef struct packed {
    bSizeT variableb; //Variable of B
} bSt;

typedef struct packed {
    readyT ready; //
} bBSt;

typedef struct packed {
    twoBitT variablec; //Two bits of C
    threeBitT variablec2; //Three bits of C
} seeSt;

typedef struct packed {
    threeBitT variabled; //Three bits of D
    fourBitT variabled2; //Four bits of D
} dSt;

typedef struct packed {
    aSizeT variablea; //One bit of A
    dSt bob; //
    seeSt [2-1:0] joe; //Need two of these
} eNestedSt;

typedef struct packed {
    bSizeT index; //
} bSizeSt;

typedef struct packed {
    aBiggerT hdr; //
} eHeaderSt;

endpackage : inAndOut_package
// GENERATED_CODE_END
