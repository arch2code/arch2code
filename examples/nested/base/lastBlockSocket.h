#ifndef LASTBLOCK_SOCKET_H
#define LASTBLOCK_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=lastBlock
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_lastBlock.base;

SC_MODULE(lastBlockSocket), public blockBase, public lastBlockBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("lastBlock_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<lastBlockSocket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    lastBlockSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~lastBlockSocket() override = default;

private:
    void betaSocket(void);
    void responseSocket(void);

// GENERATED_CODE_END
};

#endif //LASTBLOCK_SOCKET_H
