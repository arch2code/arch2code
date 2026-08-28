#ifndef PYSOCKET_SOCKET_H
#define PYSOCKET_SOCKET_H

// GENERATED_CODE_PARAM --block=pySocket
#include "asyncEvent.h"
#include "socketFactory.h"
#include "testController.h"
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "axi4_stream_port_socket.h"
#include "notify_ack_port_socket.h"
#include "pop_ack_port_socket.h"
#include "push_ack_port_socket.h"
#include "rdy_vld_port_socket.h"
#include "req_ack_port_socket.h"
#include "instanceFactory.h"
import pySocket.base;

SC_MODULE(pySocketSocket), public blockBase, public pySocketBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("pySocket_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<pySocketSocket>(blockName, variant, bbMode));}, "", "pySocket");
        }
    };
    static registerBlock registerBlock_;
public:

    pySocketSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~pySocketSocket() override = default;

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
    void test_axi4_streamSocket(void);
    void dut2Python_axi4_streamSocket(void);

// GENERATED_CODE_END
    void python2SystemCTestComplete(void);
    void systemC2PythonTestComplete(void);
    void pythonPushPopTestComplete(void);
    void pythonNotifyTestComplete(void);
    void pythonRdyVldTestComplete(void);
    void pythonAxi4StreamTestComplete(void);
    void simHeartbeat(void);
    /// Stops the kernel when end-of-test voters complete (pySocketExternal is not in the hierarchy).
    void eotStopSim(void);
};

#endif // PYSOCKET_SOCKET_H
