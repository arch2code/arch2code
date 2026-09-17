//

// GENERATED_CODE_PARAM --block=vliCont --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module vlInh_vliCont.block;
import vlInh_vliCont.base;
import vlInh.vliCont.config;
import vlInh.vliLeaf.config;
import vlInh_vliLeaf.block;
import vlInh_vliCont;
import vlInh_vliLeaf.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace vlInh_vliCont_ns;
export template<typename Config>
SC_MODULE(vliCont), public blockBase, public vliContBase<Config>
{
private:

public:
    SC_HAS_PROCESS(vliCont);

    // inherited names usable unqualified (no Config:: / this->)
    using vliContBase<Config>::VLI_ALGO;
    using vliContBase<Config>::VLI_WIDTH;
    using vliContBase<Config>::contIn;
    using vliContBase<Config>::contOut;

    // channels
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vlInh_vliLeafSourcedConfig<Config>> > out_0;
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<vlInh_vliLeafSoloConfig> > out_1;

    //instances contained in block
    std::shared_ptr<vliLeafBase<vlInh_vliLeafSourcedConfig<Config>>> uLeafA;
    std::shared_ptr<vliLeafBase<vlInh_vliLeafSourcedConfig<Config>>> uLeafB;
    std::shared_ptr<vliLeafBase<vlInh_vliLeafSoloConfig>> uLeafOrd;

    // inherited parameterized types usable unqualified (no <Config>)
    using typename vliContBase<Config>::vliPixelT;
    using typename vliContBase<Config>::vliSt;

    vliCont(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~vliCont() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
vliCont<Config>::vliCont(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("vliCont", name(), bbMode)
        ,vliContBase<Config>(name(), variant)
        ,out_0("vliLeaf_out_0", "vliLeaf")
        ,out_1("vliLeaf_out_1", "vliLeaf")
        ,uLeafA(std::dynamic_pointer_cast<vliLeafBase<vlInh_vliLeafSourcedConfig<Config>>>(instanceFactory::createInstance<vliLeaf<vlInh_vliLeafSourcedConfig<Config>>>(name(), "uLeafA", "vliLeaf", variant, "vlInh.vlInh_vliCont.vlInh_vliLeaf")))
        ,uLeafB(std::dynamic_pointer_cast<vliLeafBase<vlInh_vliLeafSourcedConfig<Config>>>(instanceFactory::createInstance<vliLeaf<vlInh_vliLeafSourcedConfig<Config>>>(name(), "uLeafB", "vliLeaf", variant, "vlInh.vlInh_vliCont.vlInh_vliLeaf")))
        ,uLeafOrd(std::dynamic_pointer_cast<vliLeafBase<vlInh_vliLeafSoloConfig>>(instanceFactory::createInstance(name(), "uLeafOrd", "vliLeaf", "solo", "vlInh.vlInh_vliCont.vlInh_vliLeaf")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uLeafA->in(this->contIn);
    uLeafB->out(this->contOut);
    // instance to instance connections via channel
    uLeafA->out(out_0);
    uLeafB->in(out_0);
    uLeafOrd->out(out_1);
    uLeafOrd->in(out_1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
