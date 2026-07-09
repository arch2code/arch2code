
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --context=ip/ipTop.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package ipTop_package;
// Generated Import package statement(s)
import ip_package::*;

// types
typedef logic[1-1:0] ipStdMarkerT; //Boundary marker bit; matches ipDataSt::marker
typedef logic[8-1:0] ipStdData8T; //Non-param 8-bit boundary payload; matches ipDataSt::data @variant0

// enums
typedef enum logic[1-1:0] {        //Generated type for addressing ipStd instances
    ADDR_ID_IPSTD_UIP = 0   // uIp instance address
} addr_id_ipstd;

// structures
typedef struct packed {
    ipStdMarkerT marker; //Marker bit; matches ipDataSt::marker
    ipStdData8T data; //8-bit payload; matches ipDataSt::data @variant0
} ipStdData8St;

endpackage : ipTop_package
// GENERATED_CODE_END
