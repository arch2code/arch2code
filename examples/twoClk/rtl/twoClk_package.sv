
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=twoClk --context=../../yaml/twoClk.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package twoClk_package;
// Generated Import package statement(s)
import twoClkIp_package::*;
localparam int unsigned TWO_CLK_TICK_DIV = 32'h0000_0004;  // clkSlow cycles between consecutive tick words
localparam int unsigned TWO_CLK_TICK_WORDS = 32'h0000_0004;  // Tick words the slow sink checks before voting end-of-test
localparam int unsigned TWO_CLK_SLOW_PERIOD_NS = 32'h0000_0003;  // clkSlow period in ns; must equal clocks.clkSlow.period in prj/yaml/project.yaml
localparam int unsigned TWO_CLK_TBL_WORDS = 32'h0000_0008;  // Row count of twoClkTable's tbl memory
localparam int unsigned TWO_CLK_TBL_WORDS_LOG2 = 32'h0000_0003;  // tbl row address width in bits
localparam int unsigned TWO_CLK_REG_ADDR_WIDTH = 32'h0000_0020;  // twoClkReg address bus width
localparam int unsigned TWO_CLK_REG_DATA_WIDTH = 32'h0000_0020;  // twoClkReg data bus width
localparam int unsigned TWO_CLK_RESET_SETTLE_NS = 32'h0000_0064;  // cpu start delay so both rst_n and rstSlow_n have released before the first bridged access

// types
typedef logic[TWO_CLK_REG_ADDR_WIDTH-1:0] twoClkRegAddrT; //for addressing a register via twoClkReg
typedef logic[TWO_CLK_REG_DATA_WIDTH-1:0] twoClkRegDataT; //for data sent or received via twoClkReg
typedef logic[TWO_CLK_TBL_WORDS_LOG2-1:0] twoClkTblAddrBitsT; //size of tbl's row address in bits
typedef logic[32-1:0] twoClkTblLoT; //tbl row bits [31:0]
typedef logic[16-1:0] twoClkTblHiT; //tbl row bits [47:32]

// enums
typedef enum logic[1-1:0] {          //Generated type for addressing tbl instances
    ADDR_ID_TBL_UTABLE = 0  // uTable instance address
} addr_id_tbl;

// structures
typedef struct packed {
    twoClkRegAddrT address; //
} twoClkRegAddrSt;

typedef struct packed {
    twoClkRegDataT data; //
} twoClkRegDataSt;

typedef struct packed {
    twoClkTblAddrBitsT address; //
} twoClkTblAddrSt;

typedef struct packed {
    twoClkTblHiT hi; //row bits [47:32]
    twoClkTblLoT lo; //row bits [31:0]
} twoClkTblSt;

endpackage : twoClk_package
// GENERATED_CODE_END
