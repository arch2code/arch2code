
// 
// GENERATED_CODE_PARAM --context=axi4sDemo_tb.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package axi4sDemo_tb_package;

// types
typedef logic[4-1:0] bv4_t; //Bit Vector 4 bits
typedef logic[8-1:0] bv8_t; //Bit Vector 8 bits
typedef logic[16-1:0] bv16_t; //Bit Vector 16 bits
typedef logic[64-1:0] bv64_t; //Bit Vector 64 bits
typedef logic[256-1:0] bv256_t; //Bit Vector 256 bits

// enums

// structures
typedef struct packed {
    bv256_t data; //
} data_t1_t;

typedef struct packed {
    bv4_t tid; //
} tid_t1_t;

typedef struct packed {
    bv4_t tid; //
} tdest_t1_t;

typedef struct packed {
    bv16_t parity; //
} tuser_t1_t;

typedef struct packed {
    bv64_t data; //
} data_t2_t;

typedef struct packed {
    bv4_t tid; //
} tid_t2_t;

typedef struct packed {
    bv4_t tid; //
} tdest_t2_t;

typedef struct packed {
    bv4_t parity; //
} tuser_t2_t;

endpackage : axi4sDemo_tb_package
// GENERATED_CODE_END
