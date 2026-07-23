
// 
// GENERATED_CODE_PARAM --context=../../yaml/hierVlSharedTypes.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package hierVlSharedTypes_package;

// types
typedef logic[8-1:0] shared_bv8_t; //Shared 8-bit vector
typedef logic[32-1:0] shared_bv32_t; //Shared 32-bit vector

// enums

// structures
typedef struct packed {
    shared_bv8_t tag; //
    shared_bv32_t value; //
} sharedInfoSt;

endpackage : hierVlSharedTypes_package
// GENERATED_CODE_END
