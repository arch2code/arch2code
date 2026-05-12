// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "helloWorldTestbench.h"

helloWorldTestbench::registerBlock helloWorldTestbench::registerBlock_; //register the block with the factory

helloWorldTestbench::helloWorldTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("helloWorldTestbench", name(), bbMode)
        ,helloWorldChannels("Chnl", "tb")
        ,helloWorld(std::dynamic_pointer_cast<helloWorldBase>( instanceFactory::createInstance(name(), "helloWorld", "helloWorld", "")))
        ,external("external")
{
    bind(helloWorld.get(), &external);
}
// GENERATED_CODE_END
