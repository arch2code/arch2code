//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockF --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
#include "status_channel.h"
#include "addressMap.h"
#include "hwMemory.h"
// GENERATED_CODE_END
#include "testController.h"

// GENERATED_CODE_BEGIN --template=moduleExport
export module mixed_blockF.block;
import mixed_blockF.base;
import mixed.blockF.config;
import mixed_mixedBlockC;
import mixed;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace mixed_mixedBlockC_ns;
using namespace mixed_ns;
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
    using blockFBase<Config>::rwArr;


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
    void rwWatch(size_t i, status_in<dRegSt>& p);

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
    for (size_t i = 0; i < REGARR_N; i++) {
        sc_spawn([this, i]() { rwWatch(i, rwArr[i]); }, sc_gen_unique_name("rwWatch", false));
    }
};

template<typename Config>
void blockF<Config>::rwWatch(size_t i, status_in<dRegSt>& p)
{
    while (true) {
        dRegSt v = p->read();
        log_.logPrint(std::format("{} rwArr[{}] = 0x{:02x}", this->name(), i, static_cast<unsigned>(v.d)), LOG_ALWAYS);
        // Encodes the stimulus of test_reg_cpu_arr: 0 or RWARR_SEED + i. Another test that writes rwArr fails here.
        if (v.d != 0 && v.d != RWARR_SEED + i) {
            log_.logPrint(std::format("{} rwArr[{}] expected 0x{:02x}", this->name(), i, RWARR_SEED + i), LOG_ALWAYS);
            errorCode::fail("blockF rwArr element misrouted");
        }
    }
}

