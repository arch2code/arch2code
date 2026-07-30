
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=mixed --context=mixedNestedInclude.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package mixed_mixedNestedInclude_package;
localparam int unsigned DSIZE = 32'h0000_0001;  // The size of D
localparam int unsigned DSIZE2 = 32'h0000_0002;  // The size of D2

// types
typedef logic[13-1:0] dupTestT; //yet another type

// enums

// structures
typedef struct packed {
    dupTestT bob; //A test structure
} dupTestSt;

endpackage : mixed_mixedNestedInclude_package
// GENERATED_CODE_END
