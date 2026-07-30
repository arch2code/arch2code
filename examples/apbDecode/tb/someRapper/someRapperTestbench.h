#ifndef SOMERAPPER_TESTBENCH_H
#define SOMERAPPER_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import apbDecode_someRapper.base;
import apbDecode;
using namespace apbDecode_ns;
#include "someRapperExternal.h"

class someRapperTestbench: public sc_module, public blockBase, public someRapperChannels {

public:

    std::shared_ptr<someRapperBase> someRapper;
    someRapperExternal external;

    someRapperTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~someRapperTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* SOMERAPPER_TESTBENCH_H */
