
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --context=ipBridge.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package ipBridge_package;

// types
typedef logic[1-1:0] bridgeMarkerT; //Stage 8.2 1-bit marker; bit-width matches ipDataSt::marker (Stage 6.2 packed-form compatibility)
typedef logic[8-1:0] data8T; //Stage 8.2 fixed 8-bit Q10-bridge payload (matches ipDataSt::data under variant0)
typedef logic[70-1:0] data70T; //Stage 8.2 fixed 70-bit Q10-bridge payload (matches ipDataSt::data under variant1)

// enums
typedef enum logic[1-1:0] {       //Generated type for addressing bridge instances
    ADDR_ID_BRIDGE_UBRIDGEIP0 = 0, // uBridgeIp0 instance address
    ADDR_ID_BRIDGE_UBRIDGEIP1 = 1 // uBridgeIp1 instance address
} addr_id_bridge;

// structures
typedef struct packed {
    bridgeMarkerT marker; //Marker bit; bit-width matches ipDataSt::marker
    data8T data; //8-bit payload; matches ipDataSt::data under variant0
} data8St;

typedef struct packed {
    bridgeMarkerT marker; //Marker bit; bit-width matches ipDataSt::marker
    data70T data; //70-bit payload; matches ipDataSt::data under variant1
} data70St;

endpackage : ipBridge_package
// GENERATED_CODE_END
