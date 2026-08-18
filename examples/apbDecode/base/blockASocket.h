#ifndef BLOCKA_SOCKET_H
#define BLOCKA_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import apbDecode_blockA.base;

SC_MODULE(blockASocket), public blockBase, public blockABase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockA_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockASocket>(blockName, variant, bbMode));}, "", "apbDecode");
        }
    };
    static registerBlock registerBlock_;
public:

    blockASocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockASocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //BLOCKA_SOCKET_H
