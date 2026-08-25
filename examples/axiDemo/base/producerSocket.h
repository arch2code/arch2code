#ifndef PRODUCER_SOCKET_H
#define PRODUCER_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "axi4_stream_port_socket.h"
#include "axi_read_port_socket.h"
#include "axi_write_port_socket.h"
#include "instanceFactory.h"
import axiDemo_producer.base;

SC_MODULE(producerSocket), public blockBase, public producerBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("producer_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<producerSocket>(blockName, variant, bbMode));}, "", "axiDemo");
        }
    };
    static registerBlock registerBlock_;
public:

    producerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~producerSocket() override = default;

private:
    void axiRd0Socket(void);
    void axiRd1Socket(void);
    void axiRd2Socket(void);
    void axiRd3Socket(void);
    void axiWr0Socket(void);
    void axiWr1Socket(void);
    void axiWr2Socket(void);
    void axiWr3Socket(void);
    void axiStr0Socket(void);
    void axiStr1Socket(void);

// GENERATED_CODE_END
};

#endif //PRODUCER_SOCKET_H
