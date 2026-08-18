#ifndef BLOCKD_SOCKET_H
#define BLOCKD_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockD
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "req_ack_port_socket.h"
#include "status_port_socket.h"
#include "instanceFactory.h"
import mixed_blockD.base;

SC_MODULE(blockDSocket), public blockBase, public blockDBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockD_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockDSocket>(blockName, variant, bbMode));}, "", "mixed");
        }
    };
    static registerBlock registerBlock_;
public:

    blockDSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockDSocket() override = default;

private:
    void cStuffIfSocket(void);
    void dee0Socket(void);
    void dee1Socket(void);
    void outDSocket(void);
    void inDSocket(void);
    void btodSocket(void);
    void rwDObserve(void);

// GENERATED_CODE_END
};

#endif //BLOCKD_SOCKET_H
