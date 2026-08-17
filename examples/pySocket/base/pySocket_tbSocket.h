#ifndef PYSOCKET_TB_SOCKET_H
#define PYSOCKET_TB_SOCKET_H
// 

// GENERATED_CODE_PARAM --block=pySocket_tb
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import pySocket_tb.base;

SC_MODULE(pySocket_tbSocket), public blockBase, public pySocket_tbBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("pySocket_tb_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<pySocket_tbSocket>(blockName, variant, bbMode));}, "", "pySocket");
        }
    };
    static registerBlock registerBlock_;
public:

    pySocket_tbSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~pySocket_tbSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //PYSOCKET_TB_SOCKET_H
