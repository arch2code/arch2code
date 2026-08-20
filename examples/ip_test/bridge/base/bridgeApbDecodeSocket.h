#ifndef BRIDGEAPBDECODE_SOCKET_H
#define BRIDGEAPBDECODE_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeApbDecode
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "apb_port_socket.h"
#include "instanceFactory.h"
import ipBridge_bridgeApbDecode.base;

SC_MODULE(bridgeApbDecodeSocket), public blockBase, public bridgeApbDecodeBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("bridgeApbDecode_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<bridgeApbDecodeSocket>(blockName, variant, bbMode));}, "", "ipBridge");
        }
    };
    static registerBlock registerBlock_;
public:

    bridgeApbDecodeSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bridgeApbDecodeSocket() override = default;

private:
    void apbReg_uBridgeIp0Socket(void);
    void apbReg_uBridgeIp1Socket(void);

// GENERATED_CODE_END
};

#endif //BRIDGEAPBDECODE_SOCKET_H
