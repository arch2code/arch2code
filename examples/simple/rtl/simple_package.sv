
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=simple --context=simple.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package simple_package;
localparam int unsigned NUM_TAGS = 32'h0000_0020;  // number of tags
localparam int unsigned NUM_TAGS_LOG2 = 32'h0000_0005;  // log2 of number of tags

// types
typedef logic[NUM_TAGS_LOG2-1:0] tag; //tag

// enums

// structures
typedef struct packed {
    tag tagId; //tag id
} tag_st;

endpackage : simple_package
// GENERATED_CODE_END
