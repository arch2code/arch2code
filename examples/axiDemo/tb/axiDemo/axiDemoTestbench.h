#ifndef AXIDEMO_TESTBENCH_H
#define AXIDEMO_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=axiDemo
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "axiDemoBase.h"
#include "axiDemoExternal.h"

// Force-link function (active modules-mode anchor) for the testbench
// class. Referencing this symbol pulls the registration TU into static links.
void force_link_axiDemoTestbench();

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
