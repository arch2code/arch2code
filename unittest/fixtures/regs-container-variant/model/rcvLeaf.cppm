//

// GENERATED_CODE_PARAM --block=rcvLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "status_channel.h"
#include "rcvTopVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module rcvTest_rcvLeaf.block;
import rcvTest_rcvLeaf.base;
import rcvTest_rcvLeaf_regs.block;
import rcvTest_rcvTop;
import rcvTest_rcvSink.base;
import rcvTest_rcvLeaf_regs.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace rcvTest_rcvTop_ns;
export template<typename Config>
SC_MODULE(rcvLeaf), public blockBase, public rcvLeafBase<Config>
{
private:

public:
    SC_HAS_PROCESS(rcvLeaf);

    // inherited names usable unqualified (no Config:: / this->)
    using rcvLeafBase<Config>::RCV_CFG_GAIN;
    using rcvLeafBase<Config>::apbReg;

    // channels
    // Written and read back over APB
    status_channel< rcvCfgSt > cfg;

    //instances contained in block
    std::shared_ptr<rcvSinkBase> uSink;
    std::shared_ptr<rcvLeaf_regsBase<Config>> u_rcvLeaf_regs;

    rcvLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~rcvLeaf() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void reportHandlerConfig(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
rcvLeaf<Config>::rcvLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("rcvLeaf", name(), bbMode)
        ,rcvLeafBase<Config>(name(), variant)
        ,cfg("rcvLeaf_cfg", "rcvLeaf", rcvCfgSt::_packedSt(0x0))
        ,uSink(std::dynamic_pointer_cast<rcvSinkBase>(instanceFactory::createInstance(name(), "uSink", "rcvSink", "", "rcvTest")))
        ,u_rcvLeaf_regs(std::dynamic_pointer_cast<rcvLeaf_regsBase<Config>>(instanceFactory::createInstance<rcvLeaf_regs<Config>>(name(), "u_rcvLeaf_regs", "rcvLeaf_regs", "", "rcvTest")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    u_rcvLeaf_regs->apbReg(this->apbReg);
    // instance to instance connections via channel
    uSink->cfg(cfg);
    u_rcvLeaf_regs->cfg(cfg);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(reportHandlerConfig);
};

// The handler owns this block's registers, so it has to be the same Config this
// block is. Reports both gains and fails the run when they part company.
template<typename Config>
void rcvLeaf<Config>::reportHandlerConfig(void)
{
    const uint64_t ownGain = (uint64_t)RCV_CFG_GAIN;
    const uint64_t handlerGain = (uint64_t)u_rcvLeaf_regs->RCV_CFG_GAIN;
    log_.logPrint(std::format("{} gain {} handler gain {}", this->name(),
        ownGain, handlerGain), LOG_IMPORTANT);
    Q_ASSERT(handlerGain == ownGain,
             "the register handler resolved a different gain than its container, "
             "so it froze at the block's declared default instead of taking the "
             "Config of this instance");
}
