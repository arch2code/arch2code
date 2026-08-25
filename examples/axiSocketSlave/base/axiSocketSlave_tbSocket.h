#ifndef AXISOCKETSLAVE_TB_SOCKET_H
#define AXISOCKETSLAVE_TB_SOCKET_H
// 

// GENERATED_CODE_PARAM --block=axiSocketSlave_tb
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import axiSocketSlave_tb.base;

SC_MODULE(axiSocketSlave_tbSocket), public blockBase, public axiSocketSlave_tbBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("axiSocketSlave_tb_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<axiSocketSlave_tbSocket>(blockName, variant, bbMode));}, "", "axiSocketSlave");
        }
    };
    static registerBlock registerBlock_;
public:

    axiSocketSlave_tbSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiSocketSlave_tbSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //AXISOCKETSLAVE_TB_SOCKET_H
