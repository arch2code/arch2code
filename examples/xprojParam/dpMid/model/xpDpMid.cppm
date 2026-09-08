//

// GENERATED_CODE_PARAM --block=xpDpMid --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpDpMid.block;
import xpDpMid.base;
import xpDpMid.xpDpMid.config;
import xpDpMid.xpDpLeaf.config;
import xpDpLeaf.block;
import xpDpLeaf;
import xpDpLeaf.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpDpLeaf_ns;
export template<typename Config>
SC_MODULE(xpDpMid), public blockBase, public xpDpMidBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpDpMid);

    // inherited names usable unqualified (no Config:: / this->)
    using xpDpMidBase<Config>::DP_WIDTH;
    using xpDpMidBase<Config>::MID_ALGO;
    using xpDpMidBase<Config>::midIn;
    using xpDpMidBase<Config>::midOut;

    // channels
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpMid_xpDpLeafCustomerConfig<Config>> > out;

    //instances contained in block
    std::shared_ptr<xpDpLeafBase<xpDpMid_xpDpLeafCustomerConfig<Config>>> uLeafA;
    std::shared_ptr<xpDpLeafBase<xpDpMid_xpDpLeafCustomerConfig<Config>>> uLeafB;

    // cross-interface thunkers
    push_ack_port_thunker<dpSt<Config>, dpSt<xpDpMid_xpDpLeafCustomerConfig<Config>>, true> thunker_uLeafA;
    push_ack_port_thunker<dpSt<Config>, dpSt<xpDpMid_xpDpLeafCustomerConfig<Config>>, true> thunker_uLeafB;

    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpDpMidBase<Config>::dpPixelT;
    using typename xpDpMidBase<Config>::dpSt;

    xpDpMid(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDpMid() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpDpMid<Config>::xpDpMid(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpDpMid", name(), bbMode)
        ,xpDpMidBase<Config>(name(), variant)
        ,out("xpDpLeaf_out", "xpDpLeaf")
        ,uLeafA(std::dynamic_pointer_cast<xpDpLeafBase<xpDpMid_xpDpLeafCustomerConfig<Config>>>(instanceFactory::createInstance<xpDpLeaf<xpDpMid_xpDpLeafCustomerConfig<Config>>>(name(), "uLeafA", "xpDpLeaf", variant, "xpDpMid.xpDpMid.xpDpLeaf")))
        ,uLeafB(std::dynamic_pointer_cast<xpDpLeafBase<xpDpMid_xpDpLeafCustomerConfig<Config>>>(instanceFactory::createInstance<xpDpLeaf<xpDpMid_xpDpLeafCustomerConfig<Config>>>(name(), "uLeafB", "xpDpLeaf", variant, "xpDpMid.xpDpMid.xpDpLeaf")))
        ,thunker_uLeafA("thunker_uLeafA", this->midIn, uLeafA->in, name())
        ,thunker_uLeafB("thunker_uLeafB", this->midOut, uLeafB->out, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    // instance to instance connections via channel
    uLeafA->out(out);
    uLeafB->in(out);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

