#ifndef IPLEAF_H
#define IPLEAF_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ipLeaf
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "ipLeafBase.h"
#include "addressMap.h"
#include "hwMemory.h"
#include "ipLeafConfig.h"
import ipLeaf;
using namespace ipLeaf_ns;

template<typename Config>
SC_MODULE(ipLeaf), public blockBase, public ipLeafBase<Config>
{
private:

public:
    SC_HAS_PROCESS(ipLeaf);


    memories mems;
    //memories
    hwMemory< ipLeafMemSt<Config> > ipLeafMem;

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

#endif //IPLEAF_H
