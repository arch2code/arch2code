#ifndef AXI4S_S_DRV_SOCKET_H
#define AXI4S_S_DRV_SOCKET_H
// 

// GENERATED_CODE_PARAM --block=axi4s_s_drv
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import axi4sDemo_axi4s_s_drv.base;

SC_MODULE(axi4s_s_drvSocket), public blockBase, public axi4s_s_drvBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("axi4s_s_drv_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<axi4s_s_drvSocket>(blockName, variant, bbMode));}, "", "axi4sDemo");
        }
    };
    static registerBlock registerBlock_;
public:

    axi4s_s_drvSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axi4s_s_drvSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //AXI4S_S_DRV_SOCKET_H
