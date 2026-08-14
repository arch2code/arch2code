import a2c.endOfTest;
#include "pySocketSocket.h"

#include "asyncEvent.h"

#include <format>

SC_HAS_PROCESS(pySocketSocket);

pySocketSocket::registerBlock pySocketSocket::registerBlock_;

void pySocketSocket::test_req_ackSocket(void)
{
    port_socket(test_req_ack, "test_req_ack");
}

void pySocketSocket::test2Python_req_ackSocket(void)
{
    port_socket(test2Python_req_ack, "test2Python_req_ack");
}

void pySocketSocket::dut2Python_req_ackSocket(void)
{
    port_socket(dut2Python_req_ack, "dut2Python_req_ack");
}

void pySocketSocket::test_push_ackSocket(void)
{
    port_socket(test_push_ack, "test_push_ack");
}

void pySocketSocket::test_pop_ackSocket(void)
{
    port_socket(test_pop_ack, "test_pop_ack");
}

void pySocketSocket::dut2Python_push_ackSocket(void)
{
    port_socket(dut2Python_push_ack, "dut2Python_push_ack");
}

void pySocketSocket::dut2Python_pop_ackSocket(void)
{
    port_socket(dut2Python_pop_ack, "dut2Python_pop_ack");
}

void pySocketSocket::test_notify_ackSocket(void)
{
    port_socket(test_notify_ack, "test_notify_ack");
}

void pySocketSocket::dut2Python_notify_ackSocket(void)
{
    port_socket(dut2Python_notify_ack, "dut2Python_notify_ack");
}

void pySocketSocket::test_rdy_vldSocket(void)
{
    port_socket(test_rdy_vld, "test_rdy_vld");
}

void pySocketSocket::dut2Python_rdy_vldSocket(void)
{
    port_socket(dut2Python_rdy_vld, "dut2Python_rdy_vld");
}

void pySocketSocket::python2SystemCTestComplete(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController &controller = testController::GetInstance();
    const std::string test_socket = "python2SystemCTest";
    controller.register_test_name(test_socket);
    controller.wait_test(test_socket, sc_time(1, SC_NS));
    auto ev = socketFactory::getPeerClosedEvent("test_req_ack");
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
    auto ev = socketFactory::getPeerClosedEvent("test2Python_req_ack");
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
    auto ev = socketFactory::getPeerClosedEvent("test_push_ack");
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
    auto ev = socketFactory::getPeerClosedEvent("test_notify_ack");
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
    auto ev = socketFactory::getPeerClosedEvent("test_rdy_vld");
    if (ev) {
        sc_core::wait(ev->default_event());
    }
    controller.test_complete(test_socket);
    eot.setEndOfTest(true);
}

pySocketSocket::pySocketSocket(sc_module_name blockName, const char *variant, blockBaseMode bbMode)
    : sc_module(blockName)
    , blockBase("pySocket", name(), bbMode)
    , pySocketBase(name(), variant)
{
    // ThreadSafeEvent is a primitive channel; it must exist before simulation starts (including
    // the delta-cycle enumeration phase). port_socket() reuses these names via newEvent().
    (void)ThreadSafeEventFactory::newEvent("test_req_ack_req");
    (void)ThreadSafeEventFactory::newEvent("test2Python_req_ack_req");
    (void)ThreadSafeEventFactory::newEvent("dut2Python_req_ack_ack");
    (void)ThreadSafeEventFactory::newEvent("test_push_ack_push");
    (void)ThreadSafeEventFactory::newEvent("test_pop_ack_pop");
    (void)ThreadSafeEventFactory::newEvent("dut2Python_push_ack_push_ack");
    (void)ThreadSafeEventFactory::newEvent("dut2Python_pop_ack_pop_ack");
    (void)ThreadSafeEventFactory::newEvent("test_notify_ack_notify");
    (void)ThreadSafeEventFactory::newEvent("dut2Python_notify_ack_notify_ack");
    (void)ThreadSafeEventFactory::newEvent("test_rdy_vld_vld");
    (void)ThreadSafeEventFactory::newEvent("dut2Python_rdy_vld_rdy");

    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT);
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
    SC_THREAD(python2SystemCTestComplete);
    SC_THREAD(systemC2PythonTestComplete);
    SC_THREAD(pythonPushPopTestComplete);
    SC_THREAD(pythonNotifyTestComplete);
    SC_THREAD(pythonRdyVldTestComplete);
    SC_THREAD(simHeartbeat);
    SC_THREAD(eotStopSim);
}


