#ifndef AXI4SDEMO_SOCKET_H
#define AXI4SDEMO_SOCKET_H
// 

// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import axi4sDemo.base;

SC_MODULE(axi4sDemoSocket), public blockBase, public axi4sDemoBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("axi4sDemo_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<axi4sDemoSocket>(blockName, variant, bbMode));}, "", "axi4sDemo");
        }
    };
    static registerBlock registerBlock_;
public:

    axi4sDemoSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axi4sDemoSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //AXI4SDEMO_SOCKET_H
