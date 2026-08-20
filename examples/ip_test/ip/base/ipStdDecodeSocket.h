#ifndef IPSTDDECODE_SOCKET_H
#define IPSTDDECODE_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdDecode
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "apb_port_socket.h"
#include "instanceFactory.h"
import ip_ipStdDecode.base;

SC_MODULE(ipStdDecodeSocket), public blockBase, public ipStdDecodeBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("ipStdDecode_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<ipStdDecodeSocket>(blockName, variant, bbMode));}, "", "ip");
        }
    };
    static registerBlock registerBlock_;
public:

    ipStdDecodeSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipStdDecodeSocket() override = default;

private:
    void ipReg_uIpSocket(void);

// GENERATED_CODE_END
};

#endif //IPSTDDECODE_SOCKET_H
