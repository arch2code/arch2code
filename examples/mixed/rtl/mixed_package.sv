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
localparam int unsigned TESTCONST1 = 32'h0000_0001;  // A test constant
localparam int unsigned TESTCONST2 = 32'h0000_0006;  // A test constant using an enum value
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
typedef logic signed[8-1:0] signedByte_t; //Signed 8-bit type (-128 to 127)
typedef logic signed[16-1:0] signedWord_t; //Signed 16-bit type (-32768 to 32767)
typedef logic signed[32-1:0] signedDword_t; //Signed 32-bit type
typedef logic signed[4-1:0] signedNibble_t; //Signed 4-bit type (-8 to 7) for testing small signed values
typedef logic signed[3-1:0] signed3bit_t; //Signed 3-bit type (-4 to 3) non-byte-aligned
typedef logic signed[5-1:0] signed5bit_t; //Signed 5-bit type (-16 to 15) non-byte-aligned
typedef logic signed[7-1:0] signed7bit_t; //Signed 7-bit type (-64 to 63) non-byte-aligned
typedef logic signed[11-1:0] signed11bit_t; //Signed 11-bit type (-1024 to 1023) non-byte-aligned
typedef logic[5-1:0] unsigned5bit_t; //Unsigned 5-bit type for mixed testing
typedef logic[9-1:0] unsigned9bit_t; //Unsigned 9-bit type for mixed testing
typedef logic[64-1:0] bigT; //64-bit type for mixed testing
typedef logic[37-1:0] test37BitT; //37-bit type for testing non-power-of-2 memory address calculations (5 bytes, rounds to 8-byte stride)

// enums
typedef enum logic[2-1:0] {           //a test enum
    TEST1_A = 0,             // Test A
    TEST1_B = 1,             // Test B
    TEST1_C = 2             // Test C
} test1EnumT;
typedef enum logic[3-1:0] {          //Type of opcodeEnA (auto generated from encoder section)
    OPCODEATYPE_READ = 0,    // Read command
    OPCODEATYPE_WRITE = 1,   // Write command
    OPCODEATYPE_WAIT = 2,    // Wait command
    OPCODEATYPE_EVICT = 3,   // Evict command
    OPCODEATYPE_TRIM = 4    // Trim command
} opcodeEnumT;
typedef enum logic[3-1:0] {            //a test enum
    TEST_A = 0,              // Test A
    TEST_B = 5,              // Test B
    TEST_C = 2              // Test C
} testEnumT;
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
    aSizeT [ASIZE2-1:0] variablea; //One bit of A
    twoBitT variablea2; //
} aSt;

typedef struct packed {
    aSizeT variablea; //One bit of A
} aASt;

typedef struct packed {
    sevenBitT a; //
} aRegSt;

typedef struct packed {
    sevenBitT d; //
} dRegSt;

typedef struct packed {
    threeBitT variabled; //Three bits of D
    fourBitT variabled2; //Four bits of D
} dSt;

typedef struct packed {
    bigT big; //
} bigSt;

typedef struct packed {
    aSizeT variablea; //One bit of A
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

typedef struct packed {
    signedByte_t signedValue; //A signed byte value for testing
    twoBitT unsignedValue; //An unsigned two-bit value
} signedTestSt;

typedef struct packed {
    signedWord_t temp; //Temperature sensor value
    signedByte_t offset; //Calibration offset
    fourBitT flags; //Status flags
} mixedSignedSt;

typedef struct packed {
    signedNibble_t [3-1:0] values; //Array of three signed nibbles
} signedArraySt;

typedef struct packed {
    signed3bit_t field1; //3-bit signed at bit 0-2
    unsigned5bit_t field2; //5-bit unsigned at bit 3-7
    signed5bit_t field3; //5-bit signed at bit 8-12
    threeBitT field4; //3-bit unsigned at bit 13-15
} nonByteAlignedSignedSt;

typedef struct packed {
    signed7bit_t signedA; //7-bit signed field
    unsigned9bit_t unsignedB; //9-bit unsigned field
    signed11bit_t signedC; //11-bit signed field
    fourBitT unsignedD; //4-bit unsigned field
    signedByte_t signedE; //8-bit signed field to cross 32-bit boundary
} complexMixedSt;

typedef struct packed {
    signed3bit_t tiny; //Very small signed value
    signedNibble_t smallVal; //Small signed value
    signed11bit_t mediumVal; //Medium signed value
    signedWord_t largeVal; //Large signed value
} edgeCaseSignedSt;

typedef struct packed {
    signed5bit_t [4-1:0] signedVals; //Array of 4 non-byte-aligned signed values
    unsigned5bit_t [3-1:0] unsignedVals; //Array of 3 non-byte-aligned unsigned values
} mixedArraySignedSt;

typedef struct packed {
    test37BitT value37; //
} test37BitRegSt;

endpackage : mixed_package
// GENERATED_CODE_END
