#ifndef AXISOCKETMASTER_TB_SOCKET_H
#define AXISOCKETMASTER_TB_SOCKET_H
// 

// GENERATED_CODE_PARAM --block=axiSocketMaster_tb
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import axiSocketMaster_tb.base;

SC_MODULE(axiSocketMaster_tbSocket), public blockBase, public axiSocketMaster_tbBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("axiSocketMaster_tb_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<axiSocketMaster_tbSocket>(blockName, variant, bbMode));}, "", "axiSocketMaster");
        }
    };
    static registerBlock registerBlock_;
public:

    axiSocketMaster_tbSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiSocketMaster_tbSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //AXISOCKETMASTER_TB_SOCKET_H
