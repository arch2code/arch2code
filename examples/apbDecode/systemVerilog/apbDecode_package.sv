
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
// GENERATED_CODE_PARAM --context=apbDecode.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package apbDecode_package;
localparam int ASIZE = 32'h0000_001D;  // The size of A
localparam int DWORD = 32'h0000_0020;  // size of a double word
localparam int MEMORYA_WORDS = 32'h0000_0013;  // Address wordlines for memory A
localparam int MEMORYA_WORDS_LOG2 = 32'h0000_0005;  // Address wordlines for memory A log2
localparam int MEMORYA_WIDTH = 32'h0000_003F;  // Bit width of content for memory A, more than 32, less than 64
localparam int MEMORYB_WORDS = 32'h0000_0015;  // Address wordlines for memory B
localparam int MEMORYB_WORDS_LOG2 = 32'h0000_0005;  // Address wordlines for memory B log2

// types
typedef logic[37-1:0] thirtySevenBitT; //Used as a thirty seven bit register structure
typedef logic[29-1:0] aSizeT; //type of width ASIZE sizing from constant ASIZE
typedef logic[32-1:0] apbAddrT; //for addressing register via APB sizing from constant DWORD
typedef logic[32-1:0] apbDataT; //for the data sent or recieved via APB sizing from constant DWORD
typedef logic[5-1:0] aAddrBitsT; //size of memory A address in bits sizing from constant MEMORYA_WORDS_LOG2
typedef logic[63-1:0] aDataBitsT; //size of memory A data in bits sizing from constant MEMORYA_WIDTH
typedef logic[5-1:0] bAddrBitsT; //size of memory B address in bits sizing from constant MEMORYB_WORDS_LOG2
typedef logic[8-1:0] u8T; //Byte integral type
typedef logic[16-1:0] u16T; //sixteen bit integral type
typedef logic[32-1:0] u32T; //thirty two bit integral type
typedef logic[64-1:0] u64T; //sixty four bit integral type

// enums
typedef enum logic[1-1:0] {          //Generated type for addressing top instances
    ADDR_ID_TOP_UBLOCKA = 0, // uBlockA instance address
    ADDR_ID_TOP_UBLOCKB = 1 // uBlockB instance address
} addr_id_top;

// structures
typedef struct packed {
    thirtySevenBitT a; //
} aRegSt;

typedef struct packed {
    u8T fa; //[7:0] - byte 0-2
    u16T fb; //[23:8] - byte 3-4
} un0BRegSt;

typedef struct packed {
    u8T fa; //[7:0] - byte 0-3
    u32T fb; //[39:8] - byte 4-7
    u8T fc; //[47:40] - byte 8-11
} un0ARegSt;

typedef struct packed {
    aSizeT index; //
} aSizeRegSt;

typedef struct packed {
    apbAddrT address; //
} apbAddrSt;

typedef struct packed {
    apbDataT data; //
} apbDataSt;

typedef struct packed {
    aAddrBitsT address; //
} aMemAddrSt;

typedef struct packed {
    aDataBitsT data; //
} aMemSt;

typedef struct packed {
    bAddrBitsT address; //
} bMemAddrSt;

typedef struct packed {
    u32T [3-1:0] data; //
} bMemSt;

endpackage : apbDecode_package
// GENERATED_CODE_END
