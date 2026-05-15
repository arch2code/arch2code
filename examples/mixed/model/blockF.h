#ifndef BLOCKF_H
#define BLOCKF_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "blockFBase.h"
#include "addressMap.h"
#include "hwMemory.h"
#include "mixedConfig.h"
import mixedBlockC;
using namespace mixedBlockC_ns;

template<typename Config>
SC_MODULE(blockF), public blockBase, public blockFBase<Config>
{
private:

public:
    SC_HAS_PROCESS(blockF);


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

#endif //BLOCKF_H
