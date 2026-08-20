#ifndef IPBRIDGE_SOCKET_H
#define IPBRIDGE_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipBridge
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "push_ack_port_socket.h"
#include "instanceFactory.h"
import ipBridge.base;

SC_MODULE(ipBridgeSocket), public blockBase, public ipBridgeBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("ipBridge_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<ipBridgeSocket>(blockName, variant, bbMode));}, "", "ipBridge");
        }
    };
    static registerBlock registerBlock_;
public:

    ipBridgeSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipBridgeSocket() override = default;

private:
    void data8InSocket(void);
    void data70InSocket(void);

// GENERATED_CODE_END
};

#endif //IPBRIDGE_SOCKET_H
