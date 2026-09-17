#ifndef CLKGEN_TESTBENCH_H
#define CLKGEN_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkGen
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import clkGen.base;
#include "clkGenExternal.h"

class clkGenTestbench: public sc_module, public blockBase, public clkGenChannels {

public:

    std::shared_ptr<clkGenBase> clkGen;
    clkGenExternal external;

    clkGenTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~clkGenTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* CLKGEN_TESTBENCH_H */
