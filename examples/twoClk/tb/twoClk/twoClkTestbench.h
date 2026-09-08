#ifndef TWOCLK_TESTBENCH_H
#define TWOCLK_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClk
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import twoClk.base;
import twoClkIp;
using namespace twoClkIp_ns;
#include "twoClkExternal.h"

class twoClkTestbench: public sc_module, public blockBase, public twoClkChannels {

public:

    std::shared_ptr<twoClkBase> twoClk;
    twoClkExternal external;

    twoClkTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~twoClkTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* TWOCLK_TESTBENCH_H */
