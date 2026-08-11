
// 
// GENERATED_CODE_PARAM --project=xpDeparam --context=../../yaml/xpDeparamTop.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package xpDeparam_xpDeparamTop_package;
// Generated Import package statement(s)
import xpSink_package::*;
import xpFilter_package::*;
import xpGain_package::*;

// types
typedef logic[4-1:0] boundaryTagT; //Literal boundary tag; matches videoSt::tag
typedef logic[8-1:0] boundaryPixelT; //Literal boundary pixel; matches videoSt::data at PIXEL_WIDTH=8

// enums

// structures
typedef struct packed {
    boundaryTagT tag; //Sample sequence tag
    boundaryPixelT data; //Pixel payload
} boundarySt;

endpackage : xpDeparam_xpDeparamTop_package
// GENERATED_CODE_END
