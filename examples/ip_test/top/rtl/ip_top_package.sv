
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=ip_test --context=../../top/yaml/ip_top.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package ip_top_package;
// Generated Import package statement(s)
import ipBridge_package::*;
import ip_package::*;
import ipLeaf_package::*;
import src_package::*;
import shared_types_package::*;

// types
typedef logic[1-1:0] boundaryMarkerT; //Boundary marker bit; matches srcOut*St::marker and ipDataSt::marker
typedef logic[8-1:0] srcOut0BoundaryT; //Non-param 8-bit boundary payload; matches uSrc OUT0_DATA_WIDTH=8 / uIp0 IP_DATA_WIDTH=8
typedef logic[70-1:0] srcOut1BoundaryT; //Non-param 70-bit boundary payload; matches uSrc OUT1_DATA_WIDTH=70 / uIp1 IP_DATA_WIDTH=70

// enums
typedef enum logic[2-1:0] {          //Generated type for addressing top instances
    ADDR_ID_TOP_UIP0 = 0,    // uIp0 instance address
    ADDR_ID_TOP_UIP1 = 1,    // uIp1 instance address
    ADDR_ID_TOP_UBRIDGE = 2 // uBridge instance address
} addr_id_top;

// structures
typedef struct packed {
    boundaryMarkerT marker; //Marker bit; matches srcOut0St::marker / ipDataSt::marker
    srcOut0BoundaryT data; //8-bit payload; matches srcOut0St::data@variantSrc0 and ipDataSt::data@variant0
} srcOut0BoundarySt;

typedef struct packed {
    boundaryMarkerT marker; //Marker bit; matches srcOut1St::marker / ipDataSt::marker
    srcOut1BoundaryT data; //70-bit payload; matches srcOut1St::data@variantSrc0 and ipDataSt::data@variant1
} srcOut1BoundarySt;

endpackage : ip_top_package
// GENERATED_CODE_END
