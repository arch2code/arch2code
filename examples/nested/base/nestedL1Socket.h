#ifndef NESTEDL1_SOCKET_H
#define NESTEDL1_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL1
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_nestedL1.base;

SC_MODULE(nestedL1Socket), public blockBase, public nestedL1Base
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("nestedL1_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<nestedL1Socket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    nestedL1Socket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL1Socket() override = default;

private:
    void nested1Socket(void);

// GENERATED_CODE_END
};

#endif //NESTEDL1_SOCKET_H
