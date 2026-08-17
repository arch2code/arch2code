#ifndef DUT_SOCKET_H
#define DUT_SOCKET_H
// 

// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "notify_ack_port_socket.h"
#include "pop_ack_port_socket.h"
#include "push_ack_port_socket.h"
#include "rdy_vld_port_socket.h"
#include "req_ack_port_socket.h"
#include "instanceFactory.h"
import pySocket_dut.base;

SC_MODULE(dutSocket), public blockBase, public dutBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("dut_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<dutSocket>(blockName, variant, bbMode));}, "", "pySocket");
        }
    };
    static registerBlock registerBlock_;
public:

    dutSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~dutSocket() override = default;

private:
    void test_req_ackSocket(void);
    void test2Python_req_ackSocket(void);
    void dut2Python_req_ackSocket(void);
    void test_push_ackSocket(void);
    void test_pop_ackSocket(void);
    void dut2Python_push_ackSocket(void);
    void dut2Python_pop_ackSocket(void);
    void test_notify_ackSocket(void);
    void dut2Python_notify_ackSocket(void);
    void test_rdy_vldSocket(void);
    void dut2Python_rdy_vldSocket(void);

// GENERATED_CODE_END
};

#endif //DUT_SOCKET_H
