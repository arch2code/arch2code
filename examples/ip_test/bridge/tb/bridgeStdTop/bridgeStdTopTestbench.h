#ifndef BRIDGESTDTOP_TESTBENCH_H
#define BRIDGESTDTOP_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeStdTop
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import ipBridge_bridgeStdTop.base;
import ipBridge;
using namespace ipBridge_ns;
import common_shared_types;
using namespace common_shared_types_ns;
#include "bridgeStdTopExternal.h"

class bridgeStdTopTestbench: public sc_module, public blockBase, public bridgeStdTopChannels {

public:

    std::shared_ptr<bridgeStdTopBase> bridgeStdTop;
    bridgeStdTopExternal external;

    bridgeStdTopTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bridgeStdTopTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* BRIDGESTDTOP_TESTBENCH_H */
