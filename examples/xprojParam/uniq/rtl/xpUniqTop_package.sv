
// 
// GENERATED_CODE_PARAM --project=xpUniq --context=../../yaml/xpUniqTop.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package xpUniq_xpUniqTop_package;
// Generated Import package statement(s)
import xpSink_xpSinkUniq_package::*;
import xpFilter_xpFilterUniq_package::*;
import xpGain_xpGainUniq_package::*;

// types
typedef logic[4-1:0] boundaryTagT; //Literal boundary tag; matches each stage's tag field
typedef logic[8-1:0] boundaryPixelT; //Literal boundary pixel; matches each stage's data field at width 8

// enums

// structures
typedef struct packed {
    boundaryTagT tag; //Sample sequence tag
    boundaryPixelT data; //Pixel payload
} boundarySt;

endpackage : xpUniq_xpUniqTop_package
// GENERATED_CODE_END
