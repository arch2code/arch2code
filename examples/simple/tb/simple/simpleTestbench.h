#ifndef SIMPLE_TESTBENCH_H
#define SIMPLE_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "simpleBase.h"
#include "simpleExternal.h"

// Force-link function (active modules-mode anchor) for the testbench
// class. Referencing this symbol pulls the registration TU into static links.
void force_link_simpleTestbench();

class simpleTestbench: public sc_module, public blockBase, public simpleChannels {

public:

    std::shared_ptr<simpleBase> simple;
    simpleExternal external;

    simpleTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~simpleTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* SIMPLE_TESTBENCH_H */
