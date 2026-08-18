#ifndef NESTEDL6_SOCKET_H
#define NESTEDL6_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL6
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_nestedL6.base;

SC_MODULE(nestedL6Socket), public blockBase, public nestedL6Base
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("nestedL6_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<nestedL6Socket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    nestedL6Socket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL6Socket() override = default;

private:
    void nested6Socket(void);

// GENERATED_CODE_END
};

#endif //NESTEDL6_SOCKET_H
