//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "addressMap.h"
#include "hwMemory.h"
#include "ipLeafVariantConfig.h"
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=moduleExport
export module ip_test_ipLeaf.block;
import ip_test_ipLeaf.base;
import ip_test_ipLeaf;
using namespace ip_test_ipLeaf_ns;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
export template<typename Config>
SC_MODULE(ipLeaf), public blockBase, public ipLeafBase<Config>
{
private:

public:
    SC_HAS_PROCESS(ipLeaf);

    // inherited names usable unqualified (no Config:: / this->)
    using ipLeafBase<Config>::LEAF_DATA_WIDTH;
    using ipLeafBase<Config>::LEAF_MEM_DEPTH;


    memories mems;
    //memories
    hwMemory< ipLeafMemSt<Config> > ipLeafMem;

    // inherited parameterized types usable unqualified (no <Config>)
    using typename ipLeafBase<Config>::ipLeafMemAddrT;
    using typename ipLeafBase<Config>::ipLeafDataT;
    using typename ipLeafBase<Config>::ipLeafMemSt;
    using typename ipLeafBase<Config>::ipLeafMemAddrSt;

    ipLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipLeaf() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ipLeafBase<Config>::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
ipLeaf<Config>::ipLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipLeaf", name(), bbMode)
        ,ipLeafBase<Config>(name(), variant)
        ,ipLeafMem(name(), "ipLeafMem", mems, Config::LEAF_MEM_DEPTH)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
