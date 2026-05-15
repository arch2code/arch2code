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

    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT);
    SC_THREAD(test_req_ackSocket);
    SC_THREAD(test2Python_req_ackSocket);
    SC_THREAD(dut2Python_req_ackSocket);
    SC_THREAD(python2SystemCTestComplete);
    SC_THREAD(systemC2PythonTestComplete);
    SC_THREAD(simHeartbeat);
    SC_THREAD(eotStopSim);
}


