
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
// GENERATED_CODE_PARAM --project=uvmReuse --context=../../yaml/uvmReuse.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package uvmReuse_package;
// Generated Import package statement(s)
import uvmReuseLeaf_package::*;
localparam int unsigned UVM_REUSE_PACKETS = 32'h0000_0004;  // Packets uDrv sends in the SystemC testbench
localparam int unsigned UVM_REUSE_PACKET_WORDS = 32'h0000_0008;  // Words per packet uDrv sends in the SystemC testbench
localparam int unsigned UVM_REUSE_TB_OFFSET_A = 32'h0000_0021;  // uLeafA offset uDrv programs
localparam int unsigned UVM_REUSE_TB_OFFSET_B = 32'h0000_0003;  // uLeafB offset uDrv programs

// types
typedef logic[8-1:0] uvmReuseCountT; //Tick count

// enums
typedef enum logic[1-1:0] { //Generated type for addressing chain instances
    ADDR_ID_UVM_REUSE_CHAIN_ULEAFA = 0, // uLeafA instance address
    ADDR_ID_UVM_REUSE_CHAIN_ULEAFB = 1 // uLeafB instance address
} addr_id_uvm_reuse_chain;

// structures
typedef struct packed {
    uvmReuseCountT count; //Tick count
} uvmReuseCountSt;

endpackage : uvmReuse_package
// GENERATED_CODE_END
