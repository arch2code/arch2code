#ifndef IPSTDMASTER_SOCKET_H
#define IPSTDMASTER_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdMaster
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "apb_port_socket.h"
#include "instanceFactory.h"
import ip_ipStdMaster.base;

SC_MODULE(ipStdMasterSocket), public blockBase, public ipStdMasterBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("ipStdMaster_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<ipStdMasterSocket>(blockName, variant, bbMode));}, "", "ip");
        }
    };
    static registerBlock registerBlock_;
public:

    ipStdMasterSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipStdMasterSocket() override = default;

private:
    void apbOutSocket(void);

// GENERATED_CODE_END
};

#endif //IPSTDMASTER_SOCKET_H
