
// 
// GENERATED_CODE_PARAM --project=xpCppAxis --context=../../yaml/xpCppWrap.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package xpCppAxis_xpCppWrap_package;
// Generated Import package statement(s)
import xpCppLeaf_package::*;

// types
typedef logic[8-1:0] wrapTagT; //Sample sequence tag
typedef logic[32-1:0] wrapWordT; //32-bit header word
typedef logic[8-1:0] wrapFlagT; //8-bit header flag

// enums

// structures
typedef struct packed {
    wrapWordT word; //Header word
    wrapFlagT flag; //Header flag
} wrapNestHdrSt;

endpackage : xpCppAxis_xpCppWrap_package
// GENERATED_CODE_END
