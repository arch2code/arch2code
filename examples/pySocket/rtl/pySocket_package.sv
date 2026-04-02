
// 
// GENERATED_CODE_PARAM --context=pySocket.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package pySocket_package;
localparam int unsigned P2S_MESSAGE_LIST_SIZE = 32'h0000_0010;  // Size of the p2s message list
localparam int unsigned P2S_MESSAGE_LIST_LOG2 = 32'h0000_0004;  // Log2 of the p2s message list size

// types
typedef logic[P2S_MESSAGE_LIST_LOG2-1:0] p2s_message_tag_t; //Tag type
typedef logic[32-1:0] param_t; //Parameter type

// enums

// structures
typedef struct packed {
    param_t param1; //Parameter 1
    param_t param2; //Parameter 2
} p2s_message_st;

typedef struct packed {
    param_t response; //response
} p2s_response_st;

typedef struct packed {
    p2s_message_tag_t tag; //Tag
} p2s_message_tag_st;

endpackage : pySocket_package
// GENERATED_CODE_END
