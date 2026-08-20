#ifndef IP_SOCKET_H
#define IP_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "push_ack_port_socket.h"
#include "instanceFactory.h"
import ip.base;
#include "ipVariantConfig.h"

template<typename Config>
SC_MODULE(ipSocket), public blockBase, public ipBase<Config>
{
private:
    struct registerBlock
    {
        registerBlock(const char * variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("ip_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<ipSocket<Config>>(blockName, variant, bbMode));}, variant_, "ip");
        }
    };
    static registerBlock registerBlock_;
public:
    SC_HAS_PROCESS(ipSocket);

    ipSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipSocket() override = default;

private:
    void ipDataIfSocket(void);

// GENERATED_CODE_END
};

#endif //IP_SOCKET_H
