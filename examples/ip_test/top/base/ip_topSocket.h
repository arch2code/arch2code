#ifndef IP_TOP_SOCKET_H
#define IP_TOP_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import ip_test_ip_top.base;

SC_MODULE(ip_topSocket), public blockBase, public ip_topBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("ip_top_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<ip_topSocket>(blockName, variant, bbMode));}, "", "ip_test");
        }
    };
    static registerBlock registerBlock_;
public:

    ip_topSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ip_topSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //IP_TOP_SOCKET_H
