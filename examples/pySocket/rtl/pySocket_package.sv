
// 
// GENERATED_CODE_PARAM --context=pySocket.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package pySocket_package;

// types
typedef logic[32-1:0] param_t; //Parameter type
typedef logic[16-1:0] word16_t; //Parameter type

// enums
typedef enum logic[1-1:0] {     //Message ID
    P2S_MESSAGE_TYPE_REQUEST = 0, // Request
    P2S_MESSAGE_TYPE_RESPONSE = 1 // Response
} p2s_message_ID_t;

// structures
typedef struct packed {
    word16_t length; //Message payload length
    word16_t ID; //Message ID
    word16_t tag; //Tag
} message_header_st;

typedef struct packed {
    param_t param2; //Parameter 2
    param_t param1; //Parameter 1
} p2s_message_st;

typedef struct packed {
    param_t response; //response
} p2s_response_st;

endpackage : pySocket_package
// GENERATED_CODE_END
