#ifndef BRIDGEDRIVER_SOCKET_H
#define BRIDGEDRIVER_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeDriver
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "push_ack_port_socket.h"
#include "instanceFactory.h"
import ipBridge_bridgeDriver.base;

SC_MODULE(bridgeDriverSocket), public blockBase, public bridgeDriverBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("bridgeDriver_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<bridgeDriverSocket>(blockName, variant, bbMode));}, "", "ipBridge");
        }
    };
    static registerBlock registerBlock_;
public:

    bridgeDriverSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bridgeDriverSocket() override = default;

private:
    void out8Socket(void);
    void out70Socket(void);

// GENERATED_CODE_END
};

#endif //BRIDGEDRIVER_SOCKET_H
