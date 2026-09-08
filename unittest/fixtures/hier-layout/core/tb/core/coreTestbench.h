#ifndef CORE_TESTBENCH_H
#define CORE_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=core
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import hier_core.base;
import hier_core;
using namespace hier_core_ns;
#include "coreExternal.h"

class coreTestbench: public sc_module, public blockBase, public coreChannels {

public:

    std::shared_ptr<coreBase> core;
    coreExternal external;

    coreTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~coreTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* CORE_TESTBENCH_H */
