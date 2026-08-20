#ifndef BRIDGESTDTOP_SOCKET_H
#define BRIDGESTDTOP_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeStdTop
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import ipBridge_bridgeStdTop.base;

SC_MODULE(bridgeStdTopSocket), public blockBase, public bridgeStdTopBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("bridgeStdTop_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<bridgeStdTopSocket>(blockName, variant, bbMode));}, "", "ipBridge");
        }
    };
    static registerBlock registerBlock_;
public:

    bridgeStdTopSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bridgeStdTopSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //BRIDGESTDTOP_SOCKET_H
