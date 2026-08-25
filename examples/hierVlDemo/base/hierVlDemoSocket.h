#ifndef HIERVLDEMO_SOCKET_H
#define HIERVLDEMO_SOCKET_H
// 

// GENERATED_CODE_PARAM --block=hierVlDemo
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "axi4_stream_port_socket.h"
#include "instanceFactory.h"
import hierVlDemo.base;

SC_MODULE(hierVlDemoSocket), public blockBase, public hierVlDemoBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("hierVlDemo_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<hierVlDemoSocket>(blockName, variant, bbMode));}, "", "hierVlDemo");
        }
    };
    static registerBlock registerBlock_;
public:

    hierVlDemoSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~hierVlDemoSocket() override = default;

private:
    void axis4_t1Socket(void);
    void axis4_t2Socket(void);

// GENERATED_CODE_END
};

#endif //HIERVLDEMO_SOCKET_H
