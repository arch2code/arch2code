#ifndef MIXED_TESTBENCH_H
#define MIXED_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "mixedBase.h"
#include "mixedExternal.h"

// Force-link function (active modules-mode anchor) for the testbench
// class. See plan-block-registration.md "Force-Link Function".
void force_link_mixedTestbench();

class mixedTestbench: public sc_module, public blockBase, public mixedChannels {

public:

    std::shared_ptr<mixedBase> mixed;
    mixedExternal external;

    mixedTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~mixedTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* MIXED_TESTBENCH_H */
