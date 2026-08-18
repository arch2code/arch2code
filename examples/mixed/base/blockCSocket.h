#ifndef BLOCKC_SOCKET_H
#define BLOCKC_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockC
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import mixed_blockC.base;

SC_MODULE(blockCSocket), public blockBase, public blockCBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockC_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockCSocket>(blockName, variant, bbMode));}, "", "mixed");
        }
    };
    static registerBlock registerBlock_;
public:

    blockCSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockCSocket() override = default;

private:
    void seeSocket(void);

// GENERATED_CODE_END
};

#endif //BLOCKC_SOCKET_H
