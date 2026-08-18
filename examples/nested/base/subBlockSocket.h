#ifndef SUBBLOCK_SOCKET_H
#define SUBBLOCK_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subBlock
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_subBlock.base;

SC_MODULE(subBlockSocket), public blockBase, public subBlockBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("subBlock_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<subBlockSocket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    subBlockSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~subBlockSocket() override = default;

private:
    void srcSocket(void);
    void dstSocket(void);

// GENERATED_CODE_END
};

#endif //SUBBLOCK_SOCKET_H
