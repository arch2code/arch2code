#ifndef BLOCKA_SOCKET_H
#define BLOCKA_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "notify_ack_port_socket.h"
#include "rdy_vld_port_socket.h"
#include "req_ack_port_socket.h"
#include "instanceFactory.h"
import mixed_blockA.base;

SC_MODULE(blockASocket), public blockBase, public blockABase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockA_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockASocket>(blockName, variant, bbMode));}, "", "mixed");
        }
    };
    static registerBlock registerBlock_;
public:

    blockASocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockASocket() override = default;

private:
    void aStuffIfSocket(void);
    void cStuffIfSocket(void);
    void startDoneSocket(void);
    void dupIfSocket(void);

// GENERATED_CODE_END
};

#endif //BLOCKA_SOCKET_H
