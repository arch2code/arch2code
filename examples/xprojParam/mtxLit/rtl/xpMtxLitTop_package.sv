
// 
// GENERATED_CODE_PARAM --project=xpMtxLit --context=../../yaml/xpMtxLitTop.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package xpMtxLit_xpMtxLitTop_package;
// Generated Import package statement(s)
import xpMtxIp_package::*;

// types
typedef logic[8-1:0] mlChTagT; //Channel tag; low packed position
typedef logic[12-1:0] mlChPixelT; //Channel pixel at the resolved endpoint width
typedef logic[8-1:0] mlChMarkT; //Channel trailing marker

// enums

// structures
typedef struct packed {
    mlChTagT tag; //Sample sequence tag
    mlChPixelT data; //Pixel payload
    mlChMarkT mark; //Trailing marker
} mlChSt;

endpackage : xpMtxLit_xpMtxLitTop_package
// GENERATED_CODE_END
