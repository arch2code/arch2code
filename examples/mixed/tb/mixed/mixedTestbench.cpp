// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "mixedTestbench.h"

mixedTestbench::registerBlock mixedTestbench::registerBlock_; //register the block with the factory

mixedTestbench::mixedTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("mixedTestbench", name(), bbMode)
        ,mixedChannels("Chnl", "tb")
        ,mixed(std::dynamic_pointer_cast<mixedBase>( instanceFactory::createInstance(name(), "mixed", "mixed", "")))
        ,external("external")
{
    bind(mixed.get(), &external);
}
// GENERATED_CODE_END
