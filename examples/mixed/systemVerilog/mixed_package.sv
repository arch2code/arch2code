// GENERATED_CODE_PARAM --context mixed.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package mixed_package;
// Generated Import package statement(s)
import mixedBlockC_package::*;
import mixedNestedInclude_package::*;
import mixedInclude_package::*;
localparam int unsigned ASIZE = 32'h0000_0001;  // The size of A
localparam int unsigned ASIZE2 = 32'h0000_0002;  // The size of A+1
localparam int unsigned INTP = 32'hFFFF_FC00;  // Test constant for numbers of unsigned integer type 
localparam int INTN = -32'sh7FFF_FC00;  // Test constant for numbers of signed integer type (two's complement negative)
localparam longint unsigned LONGP = 64'h1FFF_FFFF_FFFF_FC00;  // Test constant for numbers unsigned long type 
localparam longint LONGN = -64'sh0000_0000_FFFF_FC00;  // Test constant for numbers signed long type (two's complement negative)
localparam longint unsigned BIGE33 = 64'h0000_0001_FFFF_FFFF;  // Test constant for numbers slightly bigger than 32 bits
localparam longint unsigned BIGE53 = 64'h003F_FFFF_FFFF_FFFF;  // Test constant for numbers slightly bigger than 32 bits
localparam longint unsigned YUGE = 64'h7FFF_FFFF_FFFF_FFFF;  // Test constant for numbers of 63 bits
localparam int unsigned DWORD = 32'h0000_0020;  // size of a double word
localparam int unsigned DWORD_LOG2 = 32'h0000_0006;  // size of a double word log2
localparam int unsigned BOB0 = 32'h0000_0010;  // Memory size for instance 0
localparam int unsigned BOB1 = 32'h0000_000F;  // Memory size for instance 1
localparam int unsigned OPCODEABASE_READ = 32'h0000_0000;  // base value for Read command
localparam int unsigned OPCODEABASE_WRITE = 32'h0000_0040;  // base value for Write command
localparam int unsigned OPCODEABASE_WAIT = 32'h0000_0080;  // base value for Wait command
localparam int unsigned OPCODEABASE_EVICT = 32'h0000_00C0;  // base value for Evict command
localparam int unsigned OPCODEABASE_TRIM = 32'h0000_0100;  // base value for Trim command

// types
typedef logic[9-1:0] opcodeTagT; //opcode tag
typedef logic[2-1:0] twoBitT; //this is a 2 bit type
typedef logic[3-1:0] threeBitT; //this is a 3 bit type
typedef logic[4-1:0] fourBitT; //this is a 4 bit type
typedef logic[7-1:0] sevenBitT; //Used as a threeBitT plus a fourBitT for the register structure dRegSt
typedef logic[1-1:0] aSizeT; //type of width ASIZE sizing from constant ASIZE
typedef logic[2-1:0] aBiggerT; //yet another type sizing from constant ASIZE2
typedef logic[4-1:0] bSizeT; //for addressing memory sizing from constant BSIZE_LOG2
typedef logic[16-1:0] wordT; //a word type, used for test
typedef logic[32-1:0] apbAddrT; //for addressing register via APB sizing from constant DWORD
typedef logic[32-1:0] apbDataT; //for the data sent or recieved via APB sizing from constant DWORD

// enums
typedef enum logic[3-1:0] {          //Type of opcodeEnA (auto generated from encoder section)
    OPCODEATYPE_READ = 0,    // Read command
    OPCODEATYPE_WRITE = 1,   // Write command
    OPCODEATYPE_WAIT = 2,    // Wait command
    OPCODEATYPE_EVICT = 3,   // Evict command
    OPCODEATYPE_TRIM = 4    // Trim command
} opcodeEnumT;
typedef enum logic[1-1:0] {               //either ready or not ready
    READY_NO = 0,            // Not ready
    READY_YES = 1           // Ready
} readyT;
typedef enum logic[8-1:0] {              //opcode with fixed width
    ADD = 0,                 // Add
    SUB = 5                 // Subtract
} opcodeT;
typedef enum logic[1-1:0] {          //Generated type for addressing top instances
    ADDR_ID_TOP_UBLOCKA = 0, // uBlockA instance address
    ADDR_ID_TOP_UBLOCKB = 1 // uBlockB instance address
} addr_id_top;
typedef enum logic[2-1:0] {          //Generated type for addressing ip1 instances
    ADDR_ID_IP1_UBLOCKD = 0, // uBlockD instance address
    ADDR_ID_IP1_UBLOCKF0 = 2 // uBlockF0 instance address
} addr_id_ip1;

// structures
typedef struct packed {
    aSizeT [ASIZE2-1:0] variablea; //
    twoBitT variablea2; //
} aSt;

typedef struct packed {
    aSizeT variablea; //
} aASt;

typedef struct packed {
    sevenBitT a; //
} aRegSt;

typedef struct packed {
    sevenBitT d; //
} dRegSt;

typedef struct packed {
    threeBitT variabled; //
    fourBitT variabled2; //
} dSt;

typedef struct packed {
    aSizeT variablea; //
    dSt bob; //
    seeSt [2-1:0] joe; //Need two of these
} nestedSt;

typedef struct packed {
    bSizeT index; //
} bSizeRegSt;

typedef struct packed {
    bSizeT index; //
} bSizeSt;

typedef struct packed {
    apbAddrT address; //
} apbAddrSt;

typedef struct packed {
    apbDataT data; //
} apbDataSt;

typedef struct packed {
    sevenBitT [5-1:0] sevenBitArray; //An array of total size > 32 bit and < 64 bits
} cSt;

typedef struct packed {
    sevenBitT [5-1:0] sevenBitArray; //An array of total size > 32 bit and < 64 bits
    sevenBitT [5-1:0] sevenBitArray2; //An array of total size > 32 bit and < 64 bits
} test1St;

typedef struct packed {
    cSt [5-1:0] thirtyFiveBitArray; //An array of 35 bit * 5
} test2St;

typedef struct packed {
    aRegSt [5-1:0] sevenBitArray; //An array of 7 bit * 5
} test3St;

typedef struct packed {
    aRegSt sevenBitArray; //An array of 7 bit
} test4St;

typedef struct packed {
    aRegSt [10-1:0] sevenBitArray; //An array of 7 bit * 10
} test5St;

typedef struct packed {
    test1St largeStruct; //An array of 70 bit
} test6St;

typedef struct packed {
    test1St [5-1:0] largeStruct; //An array of 70 bit * 5
} test7St;

typedef struct packed {
    wordT [3-1:0] words; //Aligned array of 3 words, each word is 16 bits
} test8St;

typedef struct packed {
    test8St [4-1:0] wordArray; //Array of 4 * 48 bits
} test9St;

endpackage : mixed_package
// GENERATED_CODE_END
