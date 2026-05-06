// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=testbench --section=init
#include "ip_topTestbench.h"

ip_topTestbench::registerBlock ip_topTestbench::registerBlock_; //register the block with the factory

ip_topTestbench::ip_topTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("ip_topTestbench", name(), bbMode)
        ,ip_topChannels<ipDefaultConfig>("Chnl", "tb")
        ,ip_top(std::dynamic_pointer_cast<ip_topBase<ipDefaultConfig>>( instanceFactory::createInstance(name(), "ip_top", "ip_top", "")))
        ,external("external")
{
    bind(ip_top.get(), &external);
}
// GENERATED_CODE_END
