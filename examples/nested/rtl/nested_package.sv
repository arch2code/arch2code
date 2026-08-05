
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=nested --context=../../yaml/nested.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package nested_package;
localparam int unsigned NUM_COMMANDS = 32'h0000_0400;  // Number of Commands
localparam int unsigned NUM_COMMANDS_LOG2 = 32'h0000_000A;  // Number of Commands log2
localparam int unsigned BIG_WIDTH = 32'h0000_0060;  // big width test case
localparam int unsigned NUM_FIRST_TAGS = 32'h0000_0040;  // Num first Tags
localparam int unsigned NUM_FIRST_TAGS_LOG2 = 32'h0000_0006;  // Num first Tags Log2
localparam int unsigned NUM_SECOND_TAGS = 32'h0000_0400;  // Num second Tags
localparam int unsigned NUM_SECOND_TAGS_LOG2 = 32'h0000_000A;  // Num second Tags Log2
localparam int unsigned NUM_THIRD_TAGS = 32'h0000_0400;  // Num third Tags
localparam int unsigned NUM_THIRD_TAGS_LOG2 = 32'h0000_000A;  // Num third Tags Log2
localparam int unsigned NUM_TAGS = 32'h0000_0840;  // Num Tags
localparam int unsigned NUM_TAGS_LOG2 = 32'h0000_000C;  // Num Tags Log2
localparam int unsigned TAGBASE_SECONDTAG = 32'h0000_0000;  // base value for Tag type 2
localparam int unsigned TAGBASE_THIRDTAG = 32'h0000_0400;  // base value for Tag type 3
localparam int unsigned TAGBASE_FIRSTTAG = 32'h0000_0800;  // base value for Tag type 1

// types
typedef logic[NUM_TAGS_LOG2-1:0] tagT; //Read Tag
typedef logic[NUM_COMMANDS_LOG2-1:0] cmdidT; //Command ID
typedef logic[BIG_WIDTH-1:0] bigT; //big width test case
typedef logic[128-1:0] dataT; //Data
typedef logic[16-1:0] lengthT; //Length of transfer

// enums
typedef enum logic[2-1:0] {             //type of tag for encode
    TAGTYPE_SECONDTAG = 0,   // Tag type 2
    TAGTYPE_THIRDTAG = 1,    // Tag type 3
    TAGTYPE_FIRSTTAG = 2    // Tag type 1
} tagTypeT;
typedef enum logic[1-1:0] {                 //type of location for encode
    LOC_FIRSTTAG = 0,        // Tag type 1
    LOC_FLASH = 1           // Flash location
} locT;
typedef enum logic[11-1:0] {             //Example of an enum
    ENUM_TYPE_1 = 1,         // this type of enum
    ENUM_TYPE_2 = NUM_COMMANDS // other type of enum
} enumType;

// structures
typedef struct packed {
    cmdidT a; //
} test_st;

typedef struct packed {
    bigT b; //
} bigSt;

typedef struct packed {
    dataT data; //
} testDataSt;

typedef struct packed {
    cmdidT cmdid; //Command context
} testDataHdrSt;

typedef struct packed {
    lengthT length; //
} lengthHdrSt;

typedef struct packed {
    cmdidT cmdid; //Command context
} cmdidHdrSt;

endpackage : nested_package
// GENERATED_CODE_END
