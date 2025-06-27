// GENERATED_CODE_PARAM --context mixed.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package mixed_package;
// Generated Import package statement(s)
import mixedBlockC_package::*;
import mixedNestedInclude_package::*;
import mixedInclude_package::*;
//         ASIZE =                              'd1;  // The size of A
localparam ASIZE =                            32'h0000_0001;  // The size of A
//         ASIZE2 =                             'd2;  // The size of A+1
localparam ASIZE2 =                           32'h0000_0002;  // The size of A+1
//         BIGE33 =                    'd8589934591;  // Test constant for numbers slightly bigger than 32 bits
localparam BIGE33 =                  64'h0000_0001_FFFF_FFFF;  // Test constant for numbers slightly bigger than 32 bits
//         BIGE53 =             'd18014398509481983;  // Test constant for numbers slightly bigger than 32 bits
localparam BIGE53 =           64'h003F_FFFF_FFFF_FFFF;  // Test constant for numbers slightly bigger than 32 bits
//         YUGE =             'd9223372036854775807;  // Test constant for numbers of 63 bits
localparam YUGE =           64'h7FFF_FFFF_FFFF_FFFF;  // Test constant for numbers of 63 bits
//         DWORD =                             'd32;  // size of a double word
localparam DWORD =                           32'h0000_0020;  // size of a double word
//         DWORD_LOG2 =                         'd6;  // size of a double word log2
localparam DWORD_LOG2 =                       32'h0000_0006;  // size of a double word log2
//         BOB0 =                              'd16;  // Memory size for instance 0
localparam BOB0 =                            32'h0000_0010;  // Memory size for instance 0
//         BOB1 =                              'd15;  // Memory size for instance 1
localparam BOB1 =                            32'h0000_000F;  // Memory size for instance 1
//         OPCODEABASE_READ =                   'd0;  // base value for Read command
localparam OPCODEABASE_READ =                 32'h0000_0000;  // base value for Read command
//         OPCODEABASE_WRITE =                 'd64;  // base value for Write command
localparam OPCODEABASE_WRITE =               32'h0000_0040;  // base value for Write command
//         OPCODEABASE_WAIT =                 'd128;  // base value for Wait command
localparam OPCODEABASE_WAIT =               32'h0000_0080;  // base value for Wait command
//         OPCODEABASE_EVICT =                'd192;  // base value for Evict command
localparam OPCODEABASE_EVICT =              32'h0000_00C0;  // base value for Evict command
//         OPCODEABASE_TRIM =                 'd256;  // base value for Trim command
localparam OPCODEABASE_TRIM =               32'h0000_0100;  // base value for Trim command

// types
typedef logic[9-1:0] opcodeTagT; //opcode tag
typedef logic[2-1:0] twoBitT; //this is a 2 bit type
typedef logic[3-1:0] threeBitT; //this is a 3 bit type
typedef logic[4-1:0] fourBitT; //this is a 4 bit type
typedef logic[7-1:0] sevenBitT; //Used as a threeBitT plus a fourBitT for the register structure dRegSt
typedef logic[1-1:0] aSizeT; //type of width ASIZE sizing from constant ASIZE
typedef logic[2-1:0] aBiggerT; //yet another type sizing from constant ASIZE2
typedef logic[4-1:0] bSizeT; //for addressing memory sizing from constant BSIZE_LOG2
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
typedef enum logic[1-1:0] {          //Generated type for addressing ip1 instances
    ADDR_ID_IP1_UBLOCKD = 0 // uBlockD instance address
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

endpackage : mixed_package
// GENERATED_CODE_END
