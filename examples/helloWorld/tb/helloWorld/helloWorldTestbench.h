#ifndef HELLOWORLD_TESTBENCH_H
#define HELLOWORLD_TESTBENCH_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "helloWorldBase.h"
#include "helloWorldExternal.h"

class helloWorldTestbench: public sc_module, public blockBase, public helloWorldChannels {

    private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("helloWorldTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<helloWorldTestbench>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;

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
