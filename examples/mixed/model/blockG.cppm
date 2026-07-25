//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockG --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "apb_channel.h"
#include "status_channel.h"
#include "mixedVariantConfig.h"

export module blockG.block;
import blockG.base;
import mixed;
import blockGLeaf.base;
import blockGRegs.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=classDecl
using namespace mixed_ns;

export template<typename Config>
SC_MODULE(blockG), public blockBase, public blockGBase<Config>
{
private:

public:
    SC_HAS_PROCESS(blockG);

    // inherited names usable unqualified (no Config:: / this->)
    using blockGBase<Config>::fred;
    using blockGBase<Config>::apbReg;

    // channels
    // A Read Write register owned by parameterized container blockG and forwarded to a leaf
    status_channel< dRegSt > rwG;

    //instances contained in block
    std::shared_ptr<blockGLeafBase> uBlockGLeaf;
    std::shared_ptr<blockGRegsBase<mixedDefaultConfig>> uBlockGRegs;

    blockG(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockG() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
blockG<Config>::blockG(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockG", name(), bbMode)
        ,blockGBase<Config>(name(), variant)
        ,rwG("blockG_rwG", "blockG", dRegSt::_packedSt(0x0))
        ,uBlockGLeaf(std::dynamic_pointer_cast<blockGLeafBase>(instanceFactory::createInstance(name(), "uBlockGLeaf", "blockGLeaf", "", "mixed")))
        ,uBlockGRegs(std::dynamic_pointer_cast<blockGRegsBase<mixedDefaultConfig>>(instanceFactory::createInstance(name(), "uBlockGRegs", "blockGRegs", "", "mixed")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uBlockGRegs->apbReg(this->apbReg);
    // instance to instance connections via channel
    uBlockGLeaf->rwG(rwG);
    uBlockGRegs->rwG(rwG);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

