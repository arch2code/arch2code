#ifndef BLOCKB_SOCKET_H
#define BLOCKB_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import apbDecode_blockB.base;

SC_MODULE(blockBSocket), public blockBase, public blockBBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockB_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockBSocket>(blockName, variant, bbMode));}, "", "apbDecode");
        }
    };
    static registerBlock registerBlock_;
public:

    blockBSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockBSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //BLOCKB_SOCKET_H
