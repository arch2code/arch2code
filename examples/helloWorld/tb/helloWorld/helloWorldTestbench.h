#ifndef HELLOWORLD_TESTBENCH_H
#define HELLOWORLD_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "helloWorldBase.h"
#include "helloWorldExternal.h"

// Force-link function (active modules-mode anchor) for the testbench
// class. Referencing this symbol pulls the registration TU into static links.
void force_link_helloWorldTestbench();

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
