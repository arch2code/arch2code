
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=twoClkIp --context=../../yaml/twoClkIp.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package twoClkIp_package;
localparam int unsigned TWO_CLK_BURST_WORDS = 32'h0000_0004;  // Words in the twoClkIpSrc -> sink burst
localparam int unsigned TWO_CLK_BURST_BASE = 32'h0000_00A1;  // Payload of the first word of the burst; word i is BASE + i

// types
typedef logic[8-1:0] twoClkDataT; //8-bit payload word

// enums

// structures
typedef struct packed {
    twoClkDataT data; //payload word
} twoClkDataSt;

endpackage : twoClkIp_package
// GENERATED_CODE_END
