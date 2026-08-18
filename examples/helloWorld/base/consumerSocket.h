#ifndef CONSUMER_SOCKET_H
#define CONSUMER_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "pop_ack_port_socket.h"
#include "push_ack_port_socket.h"
#include "rdy_vld_port_socket.h"
#include "req_ack_port_socket.h"
#include "instanceFactory.h"
import helloWorld_consumer.base;

SC_MODULE(consumerSocket), public blockBase, public consumerBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("consumer_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<consumerSocket>(blockName, variant, bbMode));}, "", "helloWorld");
        }
    };
    static registerBlock registerBlock_;
public:

    consumerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~consumerSocket() override = default;

private:
    void test_rdy_vldSocket(void);
    void test_req_ackSocket(void);
    void test_push_ackSocket(void);
    void test_pop_ackSocket(void);

// GENERATED_CODE_END
};

#endif //CONSUMER_SOCKET_H
