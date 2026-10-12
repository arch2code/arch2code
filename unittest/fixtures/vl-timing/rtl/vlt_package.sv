
//
// GENERATED_CODE_PARAM --project=vlTiming --context=../../yaml/vlt.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package vlt_package;
localparam int unsigned VLT_START_DELAY_PS = 32'h0000_07D0;  // Source start-up delay in picoseconds, ending before the first clock edge

// types
typedef logic[32-1:0] vltStampT; //Simulation time in picoseconds

// enums

// structures
typedef struct packed {
    vltStampT stamp; //Time the source's start-up delay ended
} vltSt;

endpackage : vlt_package
// GENERATED_CODE_END
