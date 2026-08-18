#ifndef AXIDEMO_SOCKET_H
#define AXIDEMO_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=axiDemo
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import axiDemo.base;

SC_MODULE(axiDemoSocket), public blockBase, public axiDemoBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("axiDemo_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<axiDemoSocket>(blockName, variant, bbMode));}, "", "axiDemo");
        }
    };
    static registerBlock registerBlock_;
public:

    axiDemoSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiDemoSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //AXIDEMO_SOCKET_H
