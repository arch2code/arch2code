#ifndef IPSTDDRIVER_SOCKET_H
#define IPSTDDRIVER_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdDriver
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "push_ack_port_socket.h"
#include "instanceFactory.h"
import ip_ipStdDriver.base;

SC_MODULE(ipStdDriverSocket), public blockBase, public ipStdDriverBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("ipStdDriver_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<ipStdDriverSocket>(blockName, variant, bbMode));}, "", "ip");
        }
    };
    static registerBlock registerBlock_;
public:

    ipStdDriverSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipStdDriverSocket() override = default;

private:
    void out0Socket(void);

// GENERATED_CODE_END
};

#endif //IPSTDDRIVER_SOCKET_H
