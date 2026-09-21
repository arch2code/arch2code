#ifndef AXISOCKET_SOCKET_H
#define AXISOCKET_SOCKET_H
// 

// GENERATED_CODE_PARAM --block=axiSocket
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "axi_read_port_socket.h"
#include "axi_write_port_socket.h"
#include "instanceFactory.h"
import axiSocketMaster_axiSocket.base;

SC_MODULE(axiSocketSocket), public blockBase, public axiSocketBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("axiSocket_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<axiSocketSocket>(blockName, variant, bbMode));}, "", "axiSocketMaster");
        }
    };
    static registerBlock registerBlock_;
public:

    axiSocketSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiSocketSocket() override = default;

private:
    void axiRd0Socket(void);
    void axiWr0Socket(void);

// GENERATED_CODE_END
    void axiSocketMasterTestComplete(void);
    void simTimeAdvance(void);
    void eotStopSim(void);
};

#endif //AXISOCKET_SOCKET_H
