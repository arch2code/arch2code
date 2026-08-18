#ifndef TESTBLOCK_SOCKET_H
#define TESTBLOCK_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=testBlock
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_testBlock.base;

SC_MODULE(testBlockSocket), public blockBase, public testBlockBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("testBlock_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<testBlockSocket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    testBlockSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~testBlockSocket() override = default;

private:
    void loop1srcSocket(void);
    void loop1dstSocket(void);
    void loop2srcSocket(void);
    void loop2dstSocket(void);

// GENERATED_CODE_END
};

#endif //TESTBLOCK_SOCKET_H
