#ifndef IP_H
#define IP_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "ipBase.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
#include "ipConfig.h"
#include "ip_topConfig.h"
import ip;
using namespace ip_ns;
import ip_top;
using namespace ip_top_ns;

template<typename Config>
SC_MODULE(ip), public blockBase, public ipBase<Config>
{
private:
    void regHandler(void);
    addressMap regs;

public:
    SC_HAS_PROCESS(ip);


    //registers
    hwRegister< ipCfgSt<Config>, 20 > ipCfg; // IP configuration
    hwRegister< ipDataSt<Config>, 20 > ipLastData; // Last data word received on ipDataIf

    memories mems;
    //memories
    hwMemory< ipMemSt<Config> > ipMem;
    hwMemory< ipFixedSt > ipFixedMem;
    hwMemory< ipFixedSt > ipNonConstMem;

    ip(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ip() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ipBase<Config>::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END
    // block implementation members
private:
    void dataHandler(void);
};

#endif //IP_H
