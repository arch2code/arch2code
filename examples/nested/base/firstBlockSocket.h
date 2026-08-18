#ifndef FIRSTBLOCK_SOCKET_H
#define FIRSTBLOCK_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=firstBlock
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_firstBlock.base;

SC_MODULE(firstBlockSocket), public blockBase, public firstBlockBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("firstBlock_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<firstBlockSocket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    firstBlockSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~firstBlockSocket() override = default;

private:
    void primarySocket(void);
    void responseSocket(void);

// GENERATED_CODE_END
};

#endif //FIRSTBLOCK_SOCKET_H
