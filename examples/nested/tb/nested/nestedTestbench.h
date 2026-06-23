#ifndef NESTED_TESTBENCH_H
#define NESTED_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nested
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "nestedBase.h"
#include "nestedExternal.h"

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
