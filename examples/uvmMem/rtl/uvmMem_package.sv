
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=uvmMem --context=../../yaml/uvmMem.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package uvmMem_package;
localparam int unsigned UVM_MEM_WORDS = 32'h0000_0010;  // Words in the memory the wr and rd ports reach
localparam int unsigned UVM_MEM_ADDR_WIDTH = 32'h0000_0004;  // Memory address width in bits
localparam int unsigned UVM_MEM_CMDS = 32'h0000_0040;  // Commands uSrc sends in the SystemC testbench
localparam int unsigned UVM_MEM_DATA_BASE = 32'h0000_1000;  // Word uSrc's command 0 writes; command i writes UVM_MEM_DATA_BASE + i

// types
typedef logic[UVM_MEM_ADDR_WIDTH-1:0] uvmMemAddrT; //Memory word address
typedef logic[32-1:0] uvmMemDataT; //Memory word

// enums

// structures
typedef struct packed {
    uvmMemAddrT address; //
} uvmMemAddrSt;

typedef struct packed {
    uvmMemDataT word; //
} uvmMemWordSt;

typedef struct packed {
    uvmMemAddrT wrAddr; //Address the command writes
    uvmMemAddrT rdAddr; //Address the command reads before its write
    uvmMemDataT data; //Word the command writes
} uvmMemCmdSt;

endpackage : uvmMem_package
// GENERATED_CODE_END
