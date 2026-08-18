#ifndef SECONDSUBA_SOCKET_H
#define SECONDSUBA_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=secondSubA
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_secondSubA.base;

SC_MODULE(secondSubASocket), public blockBase, public secondSubABase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("secondSubA_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<secondSubASocket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    secondSubASocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~secondSubASocket() override = default;

private:
    void testSocket(void);
    void primarySocket(void);

// GENERATED_CODE_END
};

#endif //SECONDSUBA_SOCKET_H
