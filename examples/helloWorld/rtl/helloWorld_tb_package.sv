
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --context=helloWorld_tb.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package helloWorld_tb_package;
localparam int unsigned BUFFER_SIZE = 32'h0000_0040;  // Buffer size

// types
typedef logic[8-1:0] byteT; //Byte
typedef logic[64-1:0] qwordT; //64 bits

// enums

// structures
typedef struct packed {
    byteT a; //
} test_st;

typedef struct packed {
    byteT a; //
} test_no_tracker_st;

typedef struct packed {
    qwordT b; //
} data_st;

endpackage : helloWorld_tb_package
// GENERATED_CODE_END
