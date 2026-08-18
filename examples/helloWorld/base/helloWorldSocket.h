#ifndef HELLOWORLD_SOCKET_H
#define HELLOWORLD_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import helloWorld.base;

SC_MODULE(helloWorldSocket), public blockBase, public helloWorldBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("helloWorld_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<helloWorldSocket>(blockName, variant, bbMode));}, "", "helloWorld");
        }
    };
    static registerBlock registerBlock_;
public:

    helloWorldSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~helloWorldSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //HELLOWORLD_SOCKET_H
