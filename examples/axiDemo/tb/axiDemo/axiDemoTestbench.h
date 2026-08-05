#ifndef AXIDEMO_TESTBENCH_H
#define AXIDEMO_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=axiDemo
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import axiDemo.base;
import axiDemo;
using namespace axiDemo_ns;
#include "axiDemoExternal.h"

class axiDemoTestbench: public sc_module, public blockBase, public axiDemoChannels {

public:

    std::shared_ptr<axiDemoBase> axiDemo;
    axiDemoExternal external;

    axiDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiDemoTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* AXIDEMO_TESTBENCH_H */
