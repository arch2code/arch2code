#ifndef BLOCKBREGS_SOCKET_H
#define BLOCKBREGS_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockBRegs
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "status_port_socket.h"
#include "instanceFactory.h"
import mixed_blockBRegs.base;

SC_MODULE(blockBRegsSocket), public blockBase, public blockBRegsBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockBRegs_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockBRegsSocket>(blockName, variant, bbMode));}, "", "mixed");
        }
    };
    static registerBlock registerBlock_;
public:

    blockBRegsSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockBRegsSocket() override = default;

private:
    void roBsizeObserve(void);

// GENERATED_CODE_END
};

#endif //BLOCKBREGS_SOCKET_H
