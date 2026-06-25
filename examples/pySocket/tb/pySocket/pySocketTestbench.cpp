// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "pySocketTestbench.h"

pySocketTestbench::registerBlock pySocketTestbench::registerBlock_; //register the block with the factory

pySocketTestbench::pySocketTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("pySocketTestbench", name(), bbMode)
        ,pySocketChannels("Chnl", "tb")
        ,pySocket(std::dynamic_pointer_cast<pySocketBase>( instanceFactory::createInstance(name(), "pySocket", "pySocket", "")))
        ,external("external")
{
    bind(pySocket.get(), &external);
}
// GENERATED_CODE_END
