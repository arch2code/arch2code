
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=simple_ip --context=../../yaml/simple_ip.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package simple_ip_package;
// Generated Import package statement(s)
import ip_package::*;
import shared_types_package::*;

// types
typedef logic[1-1:0] simpleMarkerT; //Boundary marker bit; matches ipDataSt::marker
typedef logic[8-1:0] simpleData8T; //8-bit boundary payload; matches ipDataSt::data @variant0

// enums
typedef enum logic[1-1:0] {          //Generated type for addressing top instances
    ADDR_ID_TOP_UIP = 0     // uIp instance address
} addr_id_top;

// structures
typedef struct packed {
    simpleMarkerT marker; //marker bit
    simpleData8T data; //8-bit payload @variant0
} simpleData8St;

endpackage : simple_ip_package
// GENERATED_CODE_END
