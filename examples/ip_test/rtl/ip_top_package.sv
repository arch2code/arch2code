
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --context=ip_top.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package ip_top_package;
// Generated Import package statement(s)
import ipLeaf_package::*;
import ip_package::*;
localparam int unsigned DWORD = 32'h0000_0020;  // Width of an APB dword

// types
typedef logic[DWORD-1:0] apbAddrT; //APB address
typedef logic[DWORD-1:0] apbDataT; //APB data

// enums
typedef enum logic[1-1:0] {          //Generated type for addressing top instances
    ADDR_ID_TOP_UIP0 = 0,    // uIp0 instance address
    ADDR_ID_TOP_UIP1 = 1    // uIp1 instance address
} addr_id_top;

// structures
typedef struct packed {
    apbAddrT address; //
} apbAddrSt;

typedef struct packed {
    apbDataT data; //
} apbDataSt;

endpackage : ip_top_package
// GENERATED_CODE_END
