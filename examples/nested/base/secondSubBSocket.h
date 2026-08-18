#ifndef SECONDSUBB_SOCKET_H
#define SECONDSUBB_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=secondSubB
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "instanceFactory.h"
import nested_secondSubB.base;

SC_MODULE(secondSubBSocket), public blockBase, public secondSubBBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("secondSubB_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<secondSubBSocket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    secondSubBSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~secondSubBSocket() override = default;

private:
    void testSocket(void);
    void betaSocket(void);

// GENERATED_CODE_END
};

#endif //SECONDSUBB_SOCKET_H
