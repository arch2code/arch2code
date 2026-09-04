//

// GENERATED_CODE_PARAM --block=xpInhCont --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xpInhContVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpInhVar_xpInhCont.block;
import xpInhVar_xpInhCont.base;
import xpInhVar_xpInhLeaf.block;
import xpInhVar_xpInhCont;
import xpInhVar_xpInhLeaf.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpInhVar_xpInhCont_ns;
export template<typename Config>
SC_MODULE(xpInhCont), public blockBase, public xpInhContBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpInhCont);

    // inherited names usable unqualified (no Config:: / this->)
    using xpInhContBase<Config>::INH_ALGO;
    using xpInhContBase<Config>::INH_WIDTH;
    using xpInhContBase<Config>::contIn;
    using xpInhContBase<Config>::contOut;

    // channels
    // Parameterized pixel push/ack stream
    push_ack_channel< inhSt<Config> > out;

    //instances contained in block
    std::shared_ptr<xpInhLeafBase<Config>> uLeafA;
    std::shared_ptr<xpInhLeafBase<Config>> uLeafB;

    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpInhContBase<Config>::inhPixelT;
    using typename xpInhContBase<Config>::inhSt;

    xpInhCont(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpInhCont() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpInhCont<Config>::xpInhCont(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpInhCont", name(), bbMode)
        ,xpInhContBase<Config>(name(), variant)
        ,out("xpInhLeaf_out", "xpInhLeaf")
        ,uLeafA(std::dynamic_pointer_cast<xpInhLeafBase<Config>>(instanceFactory::createInstance<xpInhLeaf<Config>>(name(), "uLeafA", "xpInhLeaf", variant, "xpInhVar.xpInhVar_xpInhCont.xpInhVar_xpInhLeaf")))
        ,uLeafB(std::dynamic_pointer_cast<xpInhLeafBase<Config>>(instanceFactory::createInstance<xpInhLeaf<Config>>(name(), "uLeafB", "xpInhLeaf", variant, "xpInhVar.xpInhVar_xpInhCont.xpInhVar_xpInhLeaf")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uLeafA->in(this->contIn);
    uLeafB->out(this->contOut);
    // instance to instance connections via channel
    uLeafA->out(out);
    uLeafB->in(out);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

