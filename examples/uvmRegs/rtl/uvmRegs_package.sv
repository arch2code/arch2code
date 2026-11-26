
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=uvmRegs --context=../../yaml/uvmRegs.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package uvmRegs_package;
localparam int unsigned UVM_REGS_WORDS = 32'h0000_0040;  // Words uDrv streams in the SystemC testbench
localparam int unsigned UVM_REGS_TAB_ROWS = 32'h0000_0008;  // Rows of uStat's tab and hist tables
localparam int unsigned UVM_REGS_IDENT = 32'h0000_A5C3;  // Value of uDeep's ident register
localparam int unsigned UVM_REGS_TB_OFFSET0 = 32'h0000_0003;  // uScale0 offset uDrv programs
localparam int unsigned UVM_REGS_TB_OFFSET1 = 32'h0000_0021;  // uScale1 offset uDrv programs
localparam int unsigned UVM_REGS_TB_TAB_STEP = 32'h0000_0111;  // uDrv programs tab row i with i times this

// types
typedef logic[16-1:0] uvmRegsWordT; //Datapath word
typedef logic[32-1:0] uvmRegsBusT; //Register bus address and data
typedef logic[3-1:0] uvmRegsIdxT; //Row of tab or hist
typedef logic[1-1:0] uvmRegsBitT; //One-bit flag
typedef logic[8-1:0] uvmRegsByteT; //Byte register

// enums
typedef enum logic[3-1:0] {     //Generated type for addressing regs instances
    ADDR_ID_UVM_REGS_USCALE0 = 0, // uScale0 instance address
    ADDR_ID_UVM_REGS_USCALE1 = 1, // uScale1 instance address
    ADDR_ID_UVM_REGS_USTAT = 3, // uStat instance address
    ADDR_ID_UVM_REGS_UBRIDGE = 4, // uBridge instance address
    ADDR_ID_UVM_REGS_UWRAP = 5 // uWrap instance address
} addr_id_uvm_regs;
typedef enum logic[1-1:0] { //Generated type for addressing bridge instances
    ADDR_ID_UVM_REGS_BRIDGE_UDEEP = 0 // uDeep instance address
} addr_id_uvm_regs_bridge;

// structures
typedef struct packed {
    uvmRegsWordT word; //Datapath word
} uvmRegsWordSt;

typedef struct packed {
    uvmRegsBusT address; //
} uvmRegsAddrSt;

typedef struct packed {
    uvmRegsBusT data; //
} uvmRegsDataSt;

typedef struct packed {
    uvmRegsBitT invert; //Invert each word after the tab
} uvmRegsModeSt;

typedef struct packed {
    uvmRegsWordT count; //Words passed, wrapping
} uvmRegsCountSt;

typedef struct packed {
    uvmRegsWordT value; //Scratch value
} uvmRegsScratchSt;

typedef struct packed {
    uvmRegsIdxT idx; //Row
} uvmRegsIdxSt;

typedef struct packed {
    uvmRegsWordT ident; //Fixed identifier
} uvmRegsIdentSt;

typedef struct packed {
    uvmRegsByteT value; //Byte
} uvmRegsByteSt;

endpackage : uvmRegs_package
// GENERATED_CODE_END
