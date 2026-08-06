#ifndef HELLOWORLD_TESTBENCH_H
#define HELLOWORLD_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import helloWorld.base;
import helloWorld_tb;
using namespace helloWorld_tb_ns;
#include "helloWorldExternal.h"

class helloWorldTestbench: public sc_module, public blockBase, public helloWorldChannels {

public:

    std::shared_ptr<helloWorldBase> helloWorld;
    helloWorldExternal external;

    helloWorldTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~helloWorldTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* HELLOWORLD_TESTBENCH_H */
