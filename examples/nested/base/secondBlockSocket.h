#ifndef SECONDBLOCK_SOCKET_H
#define SECONDBLOCK_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=secondBlock
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_secondBlock.base;

SC_MODULE(secondBlockSocket), public blockBase, public secondBlockBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("secondBlock_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<secondBlockSocket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    secondBlockSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~secondBlockSocket() override = default;

private:
    void primarySocket(void);
    void betaSocket(void);

// GENERATED_CODE_END
};

#endif //SECONDBLOCK_SOCKET_H
