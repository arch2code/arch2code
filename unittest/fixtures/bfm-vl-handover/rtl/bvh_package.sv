
//
// GENERATED_CODE_PARAM --project=bfmVlHandover --context=../../yaml/bvh.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package bvh_package;
localparam int unsigned BVH_FIFO_DEPTH = 32'h0000_0004;  // Entries in the FIFO

// types
typedef logic[16-1:0] bvhDataT; //Beat payload

// enums

// structures
typedef struct packed {
    bvhDataT data; //Beat index
} bvhBeat;

endpackage : bvh_package
// GENERATED_CODE_END
