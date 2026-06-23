#ifndef NESTED_TESTBENCH_H
#define NESTED_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nested
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "nestedBase.h"
#include "nestedExternal.h"

// Force-link function (active modules-mode anchor) for the testbench
// class. Referencing this symbol pulls the registration TU into static links.
void force_link_nestedTestbench();

class nestedTestbench: public sc_module, public blockBase, public nestedChannels {

public:

    std::shared_ptr<nestedBase> nested;
    nestedExternal external;

    nestedTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* NESTED_TESTBENCH_H */
