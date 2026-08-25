#ifndef PRODUCER_SOCKET_H
#define PRODUCER_SOCKET_H
// 

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "axi_read_port_socket.h"
#include "axi_write_port_socket.h"
#include "instanceFactory.h"
import axiSocketSlave_producer.base;

SC_MODULE(producerSocket), public blockBase, public producerBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("producer_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<producerSocket>(blockName, variant, bbMode));}, "", "axiSocketSlave");
        }
    };
    static registerBlock registerBlock_;
public:

    producerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~producerSocket() override = default;

private:
    void axiRd0Socket(void);
    void axiWr0Socket(void);

// GENERATED_CODE_END
};

#endif //PRODUCER_SOCKET_H
