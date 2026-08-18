#ifndef BLOCKGLEAF_SOCKET_H
#define BLOCKGLEAF_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockGLeaf
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "status_port_socket.h"
#include "instanceFactory.h"
import mixed_blockGLeaf.base;

SC_MODULE(blockGLeafSocket), public blockBase, public blockGLeafBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockGLeaf_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockGLeafSocket>(blockName, variant, bbMode));}, "", "mixed");
        }
    };
    static registerBlock registerBlock_;
public:

    blockGLeafSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockGLeafSocket() override = default;

private:
    void rwGObserve(void);

// GENERATED_CODE_END
};

#endif //BLOCKGLEAF_SOCKET_H
