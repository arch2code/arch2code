
// 
// GENERATED_CODE_PARAM --project=xpMtxIp --context=../../yaml/xpMtxIp.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package xpMtxIp_package;

// types
typedef logic[8-1:0] miTagT; //Sample sequence tag; low packed position
typedef logic[8-1:0] miMarkT; //Trailing marker; sits above the pixel so a wrong-width pixel shifts it
typedef logic[12-1:0] miLitPixelT; //Literal pixel word at the same resolved width as the parameterized ones

// enums

// structures
typedef struct packed {
    miTagT tag; //Sample sequence tag
    miLitPixelT data; //Literal pixel payload
    miMarkT mark; //Trailing marker
} miSrcLitSt;

typedef struct packed {
    miTagT tag; //Sample sequence tag
    miLitPixelT data; //Literal pixel payload
    miMarkT mark; //Trailing marker
} miDstLitSt;

endpackage : xpMtxIp_package
// GENERATED_CODE_END
