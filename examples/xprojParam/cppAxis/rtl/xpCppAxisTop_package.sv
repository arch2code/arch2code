
// 
// GENERATED_CODE_PARAM --project=xpCppAxis --context=../../yaml/xpCppAxisTop.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package xpCppAxis_xpCppAxisTop_package;
// Generated Import package statement(s)
import xpCppLeaf_package::*;
import xpCppAxis_xpCppWrap_package::*;

// types
typedef logic[8-1:0] bndTagT; //Literal boundary tag
typedef logic[8-1:0] bndPixelT; //Literal boundary pixel; matches the bound wrapper width
typedef logic[32-1:0] bndWordT; //Literal boundary header word
typedef logic[8-1:0] bndFlagT; //Literal boundary header flag

// enums

// structures
typedef struct packed {
    bndTagT tag; //Sample sequence tag
    bndPixelT data; //Pixel payload
} bndEqSt;

typedef struct packed {
    bndPixelT first; //Low packed position
    bndFlagT second; //High packed position
} bndOrderSt;

typedef struct packed {
    bndPixelT data; //Pixel payload
} bndSignSt;

typedef struct packed {
    bndWordT word; //Header word
    bndFlagT flag; //Header flag
    bndFlagT tail; //Trailing flag
    bndPixelT data; //Pixel payload
} bndNestSt;

endpackage : xpCppAxis_xpCppAxisTop_package
// GENERATED_CODE_END
