
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --context=common/shared_types.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package shared_types_package;
localparam int unsigned DWORD = 32'h0000_0020;  // Width of an APB dword

// types
typedef logic[DWORD-1:0] apbAddrT; //APB address
typedef logic[DWORD-1:0] apbDataT; //APB data

// enums

// structures
typedef struct packed {
    apbAddrT address; //
} apbAddrSt;

typedef struct packed {
    apbDataT data; //
} apbDataSt;

endpackage : shared_types_package
// GENERATED_CODE_END
