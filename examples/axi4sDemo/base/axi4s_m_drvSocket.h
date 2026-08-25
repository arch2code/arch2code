#ifndef AXI4S_M_DRV_SOCKET_H
#define AXI4S_M_DRV_SOCKET_H
// 

// GENERATED_CODE_PARAM --block=axi4s_m_drv
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "axi4_stream_port_socket.h"
#include "instanceFactory.h"
import axi4sDemo_axi4s_m_drv.base;

SC_MODULE(axi4s_m_drvSocket), public blockBase, public axi4s_m_drvBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("axi4s_m_drv_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<axi4s_m_drvSocket>(blockName, variant, bbMode));}, "", "axi4sDemo");
        }
    };
    static registerBlock registerBlock_;
public:

    axi4s_m_drvSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axi4s_m_drvSocket() override = default;

private:
    void axis4_t1Socket(void);

// GENERATED_CODE_END
};

#endif //AXI4S_M_DRV_SOCKET_H
