// GENERATED_CODE_PARAM --context c/hierIncludeCInclude.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package hierIncludeCInclude_package;
//         C_ANOTHER_SIZE =                    'd10;  // The size of c another size
localparam C_ANOTHER_SIZE =                  32'h0000_000A;  // The size of c another size
//         D_SIZE =                             'd3;  // The size for d
localparam D_SIZE =                           32'h0000_0003;  // The size for d

// types
typedef logic[4-1:0] cStateT; //A state machine type for blockC
typedef logic[3-1:0] dT; //D Type sizing from constant D_SIZE

// enums

// structures
typedef struct packed {
    dT d; //
} dSt;

endpackage : hierIncludeCInclude_package
// GENERATED_CODE_END
