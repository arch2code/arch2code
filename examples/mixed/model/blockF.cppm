//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockF --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
#include "status_channel.h"
#include "addressMap.h"
#include "hwMemory.h"
#include "mixedVariantConfig.h"
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=moduleExport
export module blockF.block;
import blockF.base;
import mixedBlockC;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace mixedBlockC_ns;

export template<typename Config>
SC_MODULE(blockF), public blockBase, public blockFBase<Config>
{
private:

public:
    SC_HAS_PROCESS(blockF);

    // inherited names usable unqualified (no Config:: / this->)
    using blockFBase<Config>::bob;
    using blockFBase<Config>::fred;
    using blockFBase<Config>::cStuffIf;
    using blockFBase<Config>::dStuffIf;
    using blockFBase<Config>::dSin;
    using blockFBase<Config>::dSout;
    using blockFBase<Config>::rwD;


    memories mems;
    //memories
    hwMemory< seeSt > test;

    blockF(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockF() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        blockFBase<Config>::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
blockF<Config>::blockF(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockF", name(), bbMode)
        ,blockFBase<Config>(name(), variant)
        ,test(name(), "test", mems, Config::bob)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

