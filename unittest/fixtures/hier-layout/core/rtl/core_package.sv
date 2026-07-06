
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --context=../../core/yaml/core.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package core_package;
localparam int unsigned W = 32'h0000_0008;  // data width

// types
typedef logic[W-1:0] dat; //data word

// enums

// structures
typedef struct packed {
    dat d; //data
} dat_st;

endpackage : core_package
// GENERATED_CODE_END
