#ifndef NESTEDL3_SOCKET_H
#define NESTEDL3_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL3
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_nestedL3.base;

SC_MODULE(nestedL3Socket), public blockBase, public nestedL3Base
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("nestedL3_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<nestedL3Socket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    nestedL3Socket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL3Socket() override = default;

private:
    void nested3Socket(void);

// GENERATED_CODE_END
};

#endif //NESTEDL3_SOCKET_H
