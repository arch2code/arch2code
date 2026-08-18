#ifndef NESTEDL5_SOCKET_H
#define NESTEDL5_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL5
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_nestedL5.base;

SC_MODULE(nestedL5Socket), public blockBase, public nestedL5Base
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("nestedL5_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<nestedL5Socket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    nestedL5Socket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL5Socket() override = default;

private:
    void nested5Socket(void);

// GENERATED_CODE_END
};

#endif //NESTEDL5_SOCKET_H
