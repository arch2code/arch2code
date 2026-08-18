#ifndef DATAGEN_SOCKET_H
#define DATAGEN_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dataGen
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "push_ack_port_socket.h"
#include "instanceFactory.h"
import simple_ip_dataGen.base;

SC_MODULE(dataGenSocket), public blockBase, public dataGenBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("dataGen_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<dataGenSocket>(blockName, variant, bbMode));}, "", "simple_ip");
        }
    };
    static registerBlock registerBlock_;
public:

    dataGenSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~dataGenSocket() override = default;

private:
    void outSocket(void);

// GENERATED_CODE_END
};

#endif //DATAGEN_SOCKET_H
