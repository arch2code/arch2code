#ifndef DUT_TESTBENCH_H
#define DUT_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dut --variant=dutV0
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import xif_dut.base;
import xif;
using namespace xif_ns;
#include "dutExternal.h"

class dutTestbench: public sc_module, public blockBase, public dutChannels<dutDutV0Config> {

public:

    std::shared_ptr<dutBase<dutDutV0Config>> dut;
    dutExternal external;

    dutTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~dutTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* DUT_TESTBENCH_H */
