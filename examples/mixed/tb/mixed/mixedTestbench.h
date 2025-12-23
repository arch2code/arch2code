#ifndef MIXED_TESTBENCH_H
#define MIXED_TESTBENCH_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "mixedBase.h"
#include "mixedExternal.h"

class mixedTestbench: public sc_module, public blockBase, public mixedChannels {

    private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("mixedTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<mixedTestbench>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;

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
