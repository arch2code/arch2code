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
import ip;
using namespace ip_ns;

template<typename Config>
SC_MODULE(ip), public blockBase, public ipBase<Config>
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:
    SC_HAS_PROCESS(ip);

    // inherited names usable unqualified (no Config:: / this->)
    using ipBase<Config>::IP_DATA_WIDTH;
    using ipBase<Config>::IP_MEM_DEPTH;
    using ipBase<Config>::IP_NONCONST_DEPTH;
    using ipBase<Config>::ipDataIf;
    using ipBase<Config>::regs;


    //registers
    hwRegister< ipCfgSt<Config>, 20 > ipCfg; // IP configuration
    hwRegister< ipDataSt<Config>, 20 > ipLastData; // Last data word received on ipDataIf

    memories mems;
    //memories
    hwMemory< ipMemSt<Config> > ipMem;
    hwMemory< ipFixedSt > ipFixedMem;
    hwMemory< ipFixedSt > ipNonConstMem;
    hwMemory< ipMemSt<Config> > ipDerivedDepthMem;

    // inherited parameterized types usable unqualified (no <Config>)
    using ipBase<Config>::IP_DATA_WIDTH_X2;
    using ipBase<Config>::IP_DATA_WIDTH_X4;
    using ipBase<Config>::IP_MEM_DEPTH_X2;
    using ipBase<Config>::IP_MEM_DEPTH_X4;
    using typename ipBase<Config>::ipDataT;
    using typename ipBase<Config>::ipMemAddrT;
    using typename ipBase<Config>::ipDerivedWidthT;
    using typename ipBase<Config>::ipDerivedMemAddrT;
    using typename ipBase<Config>::ipDataSt;
    using typename ipBase<Config>::ipCfgSt;
    using typename ipBase<Config>::ipMemSt;
    using typename ipBase<Config>::ipMemAddrSt;
    using typename ipBase<Config>::ipBurstSt;
    using typename ipBase<Config>::ipDerivedMemAddrSt;
    using typename ipBase<Config>::ipParamNestedSt;

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
