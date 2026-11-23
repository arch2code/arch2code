
// GENERATED_CODE_PARAM --project=uvmReuseLeaf --context=../../yaml/uvmReuseLeaf_tb.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"

export module uvmReuseLeaf_tb;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import uvmReuseLeaf;
using namespace uvmReuseLeaf_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace uvmReuseLeaf_tb_ns {
//constants

} // namespace uvmReuseLeaf_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace uvmReuseLeaf_tb_ns {
// types

} // namespace uvmReuseLeaf_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace uvmReuseLeaf_tb_ns {
// enums
enum  addr_id_uvm_reuse_leaf { //Generated type for addressing leaf instances
    ADDR_ID_UVM_REUSE_LEAF_U_UVMREUSELEAF=0 }; // u_uvmReuseLeaf instance address
inline const char* addr_id_uvm_reuse_leaf_prt( addr_id_uvm_reuse_leaf val )
{
    switch( val )
    {
        case ADDR_ID_UVM_REUSE_LEAF_U_UVMREUSELEAF: return( "ADDR_ID_UVM_REUSE_LEAF_U_UVMREUSELEAF" );
    }
    return("!!!BADENUM!!!");
}

} // namespace uvmReuseLeaf_tb_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP

// GENERATED_CODE_END
