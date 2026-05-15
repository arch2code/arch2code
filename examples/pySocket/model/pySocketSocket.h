#ifndef PYSOCKET_SOCKET_H
#define PYSOCKET_SOCKET_H

#include "instanceFactory.h"
#include "pySocketBase.h"
#include "req_ack_port_socket.h"
#include "socketFactory.h"
#include "systemc.h"
#include "testController.h"
#include "endOfTest.h"

SC_MODULE(pySocketSocket), public blockBase, public pySocketBase
{
private:
    struct registerBlock {
        registerBlock()
        {
            instanceFactory::registerBlock(
                "pySocket_socket",
                [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared<pySocketSocket>(blockName, variant, bbMode));
                },
                "");
        }
    };
    static registerBlock registerBlock_;

public:
    pySocketSocket(sc_module_name blockName, const char *variant, blockBaseMode bbMode);
    ~pySocketSocket() override = default;

private:
    void test_req_ackSocket(void);
    void test2Python_req_ackSocket(void);
    void dut2Python_req_ackSocket(void);
    void python2SystemCTestComplete(void);
    void systemC2PythonTestComplete(void);
    void simHeartbeat(void);
    /// Stops the kernel when end-of-test voters complete (pySocketExternal is not in the hierarchy).
    void eotStopSim(void);
};

#endif // PYSOCKET_SOCKET_H
