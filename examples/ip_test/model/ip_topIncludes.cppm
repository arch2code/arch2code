
// GENERATED_CODE_PARAM --context=ip_top.yaml --mode=module
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>

export module ip_top;
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
import shared_types;
import ip;
import src;
import ipLeaf;
import ipBridge;
using namespace shared_types_ns;
using namespace ip_ns;
using namespace src_ns;
using namespace ipLeaf_ns;
using namespace ipBridge_ns;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ip_top_ns {
//constants

} // namespace ip_top_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ip_top_ns {
// types

} // namespace ip_top_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ip_top_ns {
// enums
enum  addr_id_top {          //Generated type for addressing top instances
    ADDR_ID_TOP_UIP0=0,      // uIp0 instance address
    ADDR_ID_TOP_UIP1=1,      // uIp1 instance address
    ADDR_ID_TOP_UBRIDGE=2 }; // uBridge instance address
inline const char* addr_id_top_prt( addr_id_top val )
{
    switch( val )
    {
        case ADDR_ID_TOP_UIP0: return( "ADDR_ID_TOP_UIP0" );
        case ADDR_ID_TOP_UIP1: return( "ADDR_ID_TOP_UIP1" );
        case ADDR_ID_TOP_UBRIDGE: return( "ADDR_ID_TOP_UBRIDGE" );
    }
    return("!!!BADENUM!!!");
}

} // namespace ip_top_ns
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures

// GENERATED_CODE_END
