
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=uvmReuseLeaf --context=../../yaml/uvmReuseLeaf.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package uvmReuseLeaf_package;

// types
typedef logic[16-1:0] uvmReuseWordT; //One data word
typedef logic[1-1:0] uvmReuseBitT; //A one-bit flag
typedef logic[32-1:0] uvmReuseBusT; //Register bus address and data

// enums

// structures
typedef struct packed {
    uvmReuseWordT word; //Data word
    uvmReuseBitT last; //Final beat of a packet
} uvmReuseBeatSt;

typedef struct packed {
    uvmReuseBusT address; //
} uvmReuseAddrSt;

typedef struct packed {
    uvmReuseBusT data; //
} uvmReuseDataSt;

endpackage : uvmReuseLeaf_package
// GENERATED_CODE_END
