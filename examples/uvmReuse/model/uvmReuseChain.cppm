//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseChain --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmReuse_uvmReuseChain.block;
import uvmReuse_uvmReuseChain.base;
import uvmReuse.uvmReuseChain.config;
import uvmReuse.uvmReuseLeaf.config;
import uvmReuseLeaf.config;
import uvmReuseLeaf.block;
import uvmReuseLeaf;
import uvmReuse;
import uvmReuse_uvmReuseRouter.base;
import uvmReuseLeaf.base;
import uvmReuse_uvmReuseTick.base;
import uvmReuse_uvmReuseTock.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmReuseLeaf_ns;
using namespace uvmReuse_ns;
export template<typename Config>
SC_MODULE(uvmReuseChain), public blockBase, public uvmReuseChainBase<Config>
{
private:

public:
    SC_HAS_PROCESS(uvmReuseChain);

    // inherited names usable unqualified (no Config:: / this->)
    using uvmReuseChainBase<Config>::UVM_REUSE_B_W;
    using uvmReuseChainBase<Config>::in;
    using uvmReuseChainBase<Config>::out;
    using uvmReuseChainBase<Config>::apbReg;

    // channels
    // Packets, one word per beat
    rdy_vld_channel< uvmReuseBeatSt > mid;
    // Tick counts
    push_ack_channel< uvmReuseCountSt > ticks;
    // Register bus
    apb_channel< uvmReuseAddrSt, uvmReuseDataSt > apbReg_uLeafA;
    // Register bus
    apb_channel< uvmReuseAddrSt, uvmReuseDataSt > apbReg_uLeafB;

    //instances contained in block
    std::shared_ptr<uvmReuseRouterBase> uRouter;
    std::shared_ptr<uvmReuseLeafBase<uvmReuseLeafW8Config>> uLeafA;
    std::shared_ptr<uvmReuseLeafBase<uvmReuse_uvmReuseLeafFromChainConfig<Config>>> uLeafB;
    std::shared_ptr<uvmReuseTickBase> uTick;
    std::shared_ptr<uvmReuseTockBase> uTock;

    uvmReuseChain(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmReuseChain() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
uvmReuseChain<Config>::uvmReuseChain(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmReuseChain", name(), bbMode)
        ,uvmReuseChainBase<Config>(name(), variant)
        ,mid("uvmReuseLeaf_mid", "uvmReuseLeaf", BACKPRESSURE_ALLOWED)
        ,ticks("uvmReuseTock_ticks", "uvmReuseTick")
        ,apbReg_uLeafA("uvmReuseLeaf_apbReg_uLeafA", "uvmReuseRouter")
        ,apbReg_uLeafB("uvmReuseLeaf_apbReg_uLeafB", "uvmReuseRouter")
        ,uRouter(std::dynamic_pointer_cast<uvmReuseRouterBase>(instanceFactory::createInstance(name(), "uRouter", "uvmReuseRouter", "", "uvmReuse")))
        ,uLeafA(std::dynamic_pointer_cast<uvmReuseLeafBase<uvmReuseLeafW8Config>>(instanceFactory::createInstance(name(), "uLeafA", "uvmReuseLeaf", "w8", "uvmReuse.uvmReuse_uvmReuseChain.uvmReuseLeaf")))
        ,uLeafB(std::dynamic_pointer_cast<uvmReuseLeafBase<uvmReuse_uvmReuseLeafFromChainConfig<Config>>>(instanceFactory::createInstance<uvmReuseLeaf<uvmReuse_uvmReuseLeafFromChainConfig<Config>>>(name(), "uLeafB", "uvmReuseLeaf", variant, "uvmReuse.uvmReuse_uvmReuseChain.uvmReuseLeaf")))
        ,uTick(std::dynamic_pointer_cast<uvmReuseTickBase>(instanceFactory::createInstance(name(), "uTick", "uvmReuseTick", "", "uvmReuse")))
        ,uTock(std::dynamic_pointer_cast<uvmReuseTockBase>(instanceFactory::createInstance(name(), "uTock", "uvmReuseTock", "", "uvmReuse")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uLeafA->in(this->in);
    uLeafB->out(this->out);
    uRouter->apbReg(this->apbReg);
    // instance to instance connections via channel
    uLeafA->out(mid);
    uLeafB->in(mid);
    uTick->out(ticks);
    uTock->in(ticks);
    uRouter->apbReg_uLeafA(apbReg_uLeafA);
    uLeafA->apbReg(apbReg_uLeafA);
    uRouter->apbReg_uLeafB(apbReg_uLeafB);
    uLeafB->apbReg(apbReg_uLeafB);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
