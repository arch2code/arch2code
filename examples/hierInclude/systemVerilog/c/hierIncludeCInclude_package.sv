// GENERATED_CODE_PARAM --context c/hierIncludeCInclude.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package hierIncludeCInclude_package;
localparam int unsigned C_ANOTHER_SIZE = 32'h0000_000A;  // The size of c another size
localparam int unsigned D_SIZE = 32'h0000_0003;  // The size for d

// types
typedef logic[4-1:0] cStateT; //A state machine type for blockC
typedef logic[D_SIZE-1:0] dT; //D Type

// enums

// structures
typedef struct packed {
    dT d; //
} dSt;

endpackage : hierIncludeCInclude_package
// GENERATED_CODE_END
