
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=ahbDecode --context=ahbDecode.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package ahbDecode_package;
localparam int unsigned DWORD = 32'h0000_0020;  // Register bus width
localparam int unsigned TBL_WORDS = 32'h0000_0008;  // Rows in leafA's table

// types
typedef logic[DWORD-1:0] ahbAddrT; //AHB address
typedef logic[DWORD-1:0] ahbDataT; //AHB data
typedef logic[16-1:0] u16T; //sixteen bit integral type
typedef logic[32-1:0] u32T; //thirty two bit integral type
typedef logic[3-1:0] tblAddrT; //leafA table row

// enums
typedef enum logic[2-1:0] {      //Generated type for addressing top instances
    ADDR_ID_AHB_TOP_ULEAFA = 0, // uLeafA instance address
    ADDR_ID_AHB_TOP_ULEAFB = 1, // uLeafB instance address
    ADDR_ID_AHB_TOP_USUBSYS = 2 // uSubSys instance address
} addr_id_ahb_top;
typedef enum logic[1-1:0] {      //Generated type for addressing sub instances
    ADDR_ID_AHB_SUB_ULEAFC = 0 // uLeafC instance address
} addr_id_ahb_sub;

// structures
typedef struct packed {
    ahbAddrT address; //
} ahbAddrSt;

typedef struct packed {
    ahbDataT data; //
} ahbDataSt;

typedef struct packed {
    u32T value; //
} cfgRegSt;

typedef struct packed {
    u16T value; //
} statRegSt;

typedef struct packed {
    u16T value; //
} cmdRegSt;

typedef struct packed {
    u32T data; //
} tblSt;

typedef struct packed {
    tblAddrT address; //
} tblAddrSt;

endpackage : ahbDecode_package
// GENERATED_CODE_END
