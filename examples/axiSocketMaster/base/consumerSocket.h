#ifndef CONSUMER_SOCKET_H
#define CONSUMER_SOCKET_H
// 

// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "axi_read_port_socket.h"
#include "axi_write_port_socket.h"
#include "instanceFactory.h"
import axiSocketMaster_consumer.base;

SC_MODULE(consumerSocket), public blockBase, public consumerBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("consumer_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<consumerSocket>(blockName, variant, bbMode));}, "", "axiSocketMaster");
        }
    };
    static registerBlock registerBlock_;
public:

    consumerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~consumerSocket() override = default;

private:
    void axiRd0Socket(void);
    void axiWr0Socket(void);

// GENERATED_CODE_END
};

#endif //CONSUMER_SOCKET_H
