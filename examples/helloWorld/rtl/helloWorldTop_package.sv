
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
// GENERATED_CODE_PARAM --context=helloWorldTop.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package helloWorldTop_package;
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

endpackage : helloWorldTop_package
// GENERATED_CODE_END
