
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=xif --context=xif.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package xif_package;

// types
typedef logic[16-1:0] streamBndryDataT; //Non-parameterized boundary payload word (matches DATA_WIDTH=16)

// enums

// structures
typedef struct packed {
    streamBndryDataT data; //Boundary payload; packed layout matches streamSt<dutV0>
} streamBndrySt;

endpackage : xif_package
// GENERATED_CODE_END
