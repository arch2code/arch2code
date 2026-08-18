#ifndef SIMPLE_IP_SOCKET_H
#define SIMPLE_IP_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple_ip
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import simple_ip.base;

SC_MODULE(simple_ipSocket), public blockBase, public simple_ipBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("simple_ip_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<simple_ipSocket>(blockName, variant, bbMode));}, "", "simple_ip");
        }
    };
    static registerBlock registerBlock_;
public:

    simple_ipSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~simple_ipSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //SIMPLE_IP_SOCKET_H
