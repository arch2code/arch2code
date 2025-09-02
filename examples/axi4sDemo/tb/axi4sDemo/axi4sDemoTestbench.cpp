// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "axi4sDemoTestbench.h"

axi4sDemoTestbench::registerBlock axi4sDemoTestbench::registerBlock_; //register the block with the factory

axi4sDemoTestbench::axi4sDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("axi4sDemoTestbench", name(), bbMode)
        ,axi4sDemoChannels("Chnl", "tb")
        ,axi4sDemo(std::dynamic_pointer_cast<axi4sDemoBase>( instanceFactory::createInstance(name(), "axi4sDemo", "axi4sDemo", "")))
        ,external("external")
{
    bind(axi4sDemo.get(), &external);
}
// GENERATED_CODE_END
