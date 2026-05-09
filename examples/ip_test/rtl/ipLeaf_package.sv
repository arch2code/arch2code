
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --context=ipLeaf.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package ipLeaf_package;
localparam int unsigned LEAF_DATA_WIDTH = 32'h0000_0004;  // ipLeaf per-instance data width
localparam int unsigned LEAF_MEM_DEPTH = 32'h0000_0004;  // ipLeaf per-instance memory depth

// types
typedef logic[LEAF_DATA_WIDTH-1:0] ipLeafDataT; //ipLeaf data word, parameterizable
typedef logic[$clog2(LEAF_MEM_DEPTH)-1:0] ipLeafMemAddrT; //Index into ipLeaf's private memory (0..LEAF_MEM_DEPTH-1)

// enums

// structures
typedef struct packed {
    ipLeafDataT data; //Leaf memory word
} ipLeafMemSt;

typedef struct packed {
    ipLeafMemAddrT address; //Leaf memory address
} ipLeafMemAddrSt;

endpackage : ipLeaf_package
// GENERATED_CODE_END
