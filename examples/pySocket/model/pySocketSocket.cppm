//

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=socket --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "axi4_stream_port_socket.h"
#include "notify_ack_port_socket.h"
#include "pop_ack_port_socket.h"
#include "push_ack_port_socket.h"
#include "rdy_vld_port_socket.h"
#include "req_ack_port_socket.h"
#include "pySocketSocketCatalog.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "asyncEvent.h"
#include "socketFactory.h"
#include "testController.h"
#include <format>
// GENERATED_CODE_BEGIN --template=socket --section=moduleExport
export module pySocket.socket;
import pySocket.base;
import pySocket_tb;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=socket --section=socket
export SC_MODULE(pySocketSocket), public blockBase, public pySocketBase
{
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
    // socket shell members
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

// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
SC_HAS_PROCESS(pySocketSocket);

// === Socket shell factory registration (pySocketSocket) ===
void register_pySocketSocket() {
    instanceFactory::registerBlock("pySocket_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<pySocketSocket>(blockName, variant, bbMode)); }, "", "pySocket");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _pySocketSocket_registered = (register_pySocketSocket(), 0);
} // namespace
// === End socket shell factory registration ===

void pySocketSocket::test_req_ackSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_test_req_ack(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_test_req_ack(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(test_req_ack, pySocketSocketCatalog::name_test_req_ack(this->name()));
}

void pySocketSocket::test2Python_req_ackSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_test2Python_req_ack(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_test2Python_req_ack(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(test2Python_req_ack, pySocketSocketCatalog::name_test2Python_req_ack(this->name()));
}

void pySocketSocket::dut2Python_req_ackSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_dut2Python_req_ack(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_dut2Python_req_ack(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(dut2Python_req_ack, pySocketSocketCatalog::name_dut2Python_req_ack(this->name()));
}

void pySocketSocket::test_push_ackSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_test_push_ack(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_test_push_ack(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(test_push_ack, pySocketSocketCatalog::name_test_push_ack(this->name()));
}

void pySocketSocket::test_pop_ackSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_test_pop_ack(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_test_pop_ack(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(test_pop_ack, pySocketSocketCatalog::name_test_pop_ack(this->name()));
}

void pySocketSocket::dut2Python_push_ackSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_dut2Python_push_ack(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_dut2Python_push_ack(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(dut2Python_push_ack, pySocketSocketCatalog::name_dut2Python_push_ack(this->name()));
}

void pySocketSocket::dut2Python_pop_ackSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_dut2Python_pop_ack(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_dut2Python_pop_ack(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(dut2Python_pop_ack, pySocketSocketCatalog::name_dut2Python_pop_ack(this->name()));
}

void pySocketSocket::test_notify_ackSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_test_notify_ack(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_test_notify_ack(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(test_notify_ack, pySocketSocketCatalog::name_test_notify_ack(this->name()));
}

void pySocketSocket::dut2Python_notify_ackSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_dut2Python_notify_ack(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_dut2Python_notify_ack(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(dut2Python_notify_ack, pySocketSocketCatalog::name_dut2Python_notify_ack(this->name()));
}

void pySocketSocket::test_rdy_vldSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_test_rdy_vld(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_test_rdy_vld(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(test_rdy_vld, pySocketSocketCatalog::name_test_rdy_vld(this->name()));
}

void pySocketSocket::dut2Python_rdy_vldSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_dut2Python_rdy_vld(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_dut2Python_rdy_vld(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(dut2Python_rdy_vld, pySocketSocketCatalog::name_dut2Python_rdy_vld(this->name()));
}

void pySocketSocket::test_axi4_streamSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_test_axi4_stream(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_test_axi4_stream(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(test_axi4_stream, pySocketSocketCatalog::name_test_axi4_stream(this->name()));
}

void pySocketSocket::dut2Python_axi4_streamSocket(void) {
    Q_ASSERT(socketFactory::getPort(pySocketSocketCatalog::name_dut2Python_axi4_stream(this->name())) != 0,
             "socket " + pySocketSocketCatalog::name_dut2Python_axi4_stream(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(dut2Python_axi4_stream, pySocketSocketCatalog::name_dut2Python_axi4_stream(this->name()));
}

pySocketSocket::pySocketSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("pySocket", name(), bbMode)
        ,pySocketBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(test_req_ackSocket);
    SC_THREAD(test2Python_req_ackSocket);
    SC_THREAD(dut2Python_req_ackSocket);
    SC_THREAD(test_push_ackSocket);
    SC_THREAD(test_pop_ackSocket);
    SC_THREAD(dut2Python_push_ackSocket);
    SC_THREAD(dut2Python_pop_ackSocket);
    SC_THREAD(test_notify_ackSocket);
    SC_THREAD(dut2Python_notify_ackSocket);
    SC_THREAD(test_rdy_vldSocket);
    SC_THREAD(dut2Python_rdy_vldSocket);
    SC_THREAD(test_axi4_streamSocket);
    SC_THREAD(dut2Python_axi4_streamSocket);

// GENERATED_CODE_END
    // ThreadSafeEvent is a primitive channel; it must exist before simulation starts (including
    // the delta-cycle enumeration phase). port_socket() reuses these names via newEvent().
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_test_req_ack(name()) + "_req").c_str());
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_test2Python_req_ack(name()) + "_req").c_str());
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_dut2Python_req_ack(name()) + "_ack").c_str());
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_test_push_ack(name()) + "_push").c_str());
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_test_pop_ack(name()) + "_pop").c_str());
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_dut2Python_push_ack(name()) + "_push_ack").c_str());
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_dut2Python_pop_ack(name()) + "_pop_ack").c_str());
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_test_notify_ack(name()) + "_notify").c_str());
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_dut2Python_notify_ack(name()) + "_notify_ack").c_str());
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_test_rdy_vld(name()) + "_vld").c_str());
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_dut2Python_rdy_vld(name()) + "_rdy").c_str());
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_test_axi4_stream(name()) + "_axis").c_str());
    (void)ThreadSafeEventFactory::newEvent((pySocketSocketCatalog::name_dut2Python_axi4_stream(name()) + "_axis_rdy").c_str());

    SC_THREAD(python2SystemCTestComplete);
    SC_THREAD(systemC2PythonTestComplete);
    SC_THREAD(pythonPushPopTestComplete);
    SC_THREAD(pythonNotifyTestComplete);
    SC_THREAD(pythonRdyVldTestComplete);
    SC_THREAD(pythonAxi4StreamTestComplete);
    SC_THREAD(simHeartbeat);
    SC_THREAD(eotStopSim);
}
// user method definitions here

void pySocketSocket::python2SystemCTestComplete(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController &controller = testController::GetInstance();
    const std::string test_socket = "python2SystemCTest";
    controller.register_test_name(test_socket);
    controller.wait_test(test_socket, sc_time(1, SC_NS));
    auto ev = socketFactory::getPeerClosedEvent(pySocketSocketCatalog::name_test_req_ack(name()));
    if (ev) {
        sc_core::wait(ev->default_event());
    }
    controller.test_complete(test_socket);
    eot.setEndOfTest(true);
}

void pySocketSocket::simHeartbeat(void)
{
    while (true) {
        wait(sc_time(1, SC_US));
    }
}

void pySocketSocket::eotStopSim(void)
{
    testController::GetInstance().wait_all_tests_complete();
    endOfTestState &eot = endOfTestState::GetInstance();
    // Avoid missing eotEvent.notify() if it fires before this thread first waits.
    while (!eot.isEndOfTest()) {
        wait(eot.eotEvent);
    }
    sc_stop();
}

void pySocketSocket::systemC2PythonTestComplete(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController &controller = testController::GetInstance();
    const std::string test_socket = "systemC2PythonTest";
    controller.register_test_name(test_socket);
    controller.wait_test(test_socket, sc_time(1, SC_NS));
    auto ev = socketFactory::getPeerClosedEvent(pySocketSocketCatalog::name_test2Python_req_ack(name()));
    if (ev) {
        sc_core::wait(ev->default_event());
    }
    controller.test_complete(test_socket);
    eot.setEndOfTest(true);
}

void pySocketSocket::pythonPushPopTestComplete(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController &controller = testController::GetInstance();
    const std::string test_socket = "pythonPushPopTest";
    controller.register_test_name(test_socket);
    controller.wait_test(test_socket, sc_time(1, SC_NS));
    auto ev = socketFactory::getPeerClosedEvent(pySocketSocketCatalog::name_test_push_ack(name()));
    if (ev) {
        sc_core::wait(ev->default_event());
    }
    controller.test_complete(test_socket);
    eot.setEndOfTest(true);
}

void pySocketSocket::pythonNotifyTestComplete(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController &controller = testController::GetInstance();
    const std::string test_socket = "pythonNotifyTest";
    controller.register_test_name(test_socket);
    controller.wait_test(test_socket, sc_time(1, SC_NS));
    auto ev = socketFactory::getPeerClosedEvent(pySocketSocketCatalog::name_test_notify_ack(name()));
    if (ev) {
        sc_core::wait(ev->default_event());
    }
    controller.test_complete(test_socket);
    eot.setEndOfTest(true);
}

void pySocketSocket::pythonRdyVldTestComplete(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController &controller = testController::GetInstance();
    const std::string test_socket = "pythonRdyVldTest";
    controller.register_test_name(test_socket);
    controller.wait_test(test_socket, sc_time(1, SC_NS));
    auto ev = socketFactory::getPeerClosedEvent(pySocketSocketCatalog::name_test_rdy_vld(name()));
    if (ev) {
        sc_core::wait(ev->default_event());
    }
    controller.test_complete(test_socket);
    eot.setEndOfTest(true);
}

void pySocketSocket::pythonAxi4StreamTestComplete(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController &controller = testController::GetInstance();
    const std::string test_socket = "pythonAxi4StreamTest";
    controller.register_test_name(test_socket);
    controller.wait_test(test_socket, sc_time(1, SC_NS));
    auto ev = socketFactory::getPeerClosedEvent(pySocketSocketCatalog::name_test_axi4_stream(name()));
    if (ev) {
        sc_core::wait(ev->default_event());
    }
    controller.test_complete(test_socket);
    eot.setEndOfTest(true);
}
