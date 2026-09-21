import a2c.endOfTest;
// GENERATED_CODE_PARAM --block=pySocket
#include <format>
#include "pySocketSocketCatalog.h"
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "pySocketSocket.h"

SC_HAS_PROCESS(pySocketSocket);

pySocketSocket::registerBlock pySocketSocket::registerBlock_; //register the block with the factory

void pySocketSocket::test_req_ackSocket(void) {
    port_socket(test_req_ack, "pySocket.test_req_ack");
}

void pySocketSocket::test2Python_req_ackSocket(void) {
    port_socket(test2Python_req_ack, "pySocket.test2Python_req_ack");
}

void pySocketSocket::dut2Python_req_ackSocket(void) {
    port_socket(dut2Python_req_ack, "pySocket.dut2Python_req_ack");
}

void pySocketSocket::test_push_ackSocket(void) {
    port_socket(test_push_ack, "pySocket.test_push_ack");
}

void pySocketSocket::test_pop_ackSocket(void) {
    port_socket(test_pop_ack, "pySocket.test_pop_ack");
}

void pySocketSocket::dut2Python_push_ackSocket(void) {
    port_socket(dut2Python_push_ack, "pySocket.dut2Python_push_ack");
}

void pySocketSocket::dut2Python_pop_ackSocket(void) {
    port_socket(dut2Python_pop_ack, "pySocket.dut2Python_pop_ack");
}

void pySocketSocket::test_notify_ackSocket(void) {
    port_socket(test_notify_ack, "pySocket.test_notify_ack");
}

void pySocketSocket::dut2Python_notify_ackSocket(void) {
    port_socket(dut2Python_notify_ack, "pySocket.dut2Python_notify_ack");
}

void pySocketSocket::test_rdy_vldSocket(void) {
    port_socket(test_rdy_vld, "pySocket.test_rdy_vld");
}

void pySocketSocket::dut2Python_rdy_vldSocket(void) {
    port_socket(dut2Python_rdy_vld, "pySocket.dut2Python_rdy_vld");
}

void pySocketSocket::test_axi4_streamSocket(void) {
    port_socket(test_axi4_stream, "pySocket.test_axi4_stream");
}

void pySocketSocket::dut2Python_axi4_streamSocket(void) {
    port_socket(dut2Python_axi4_stream, "pySocket.dut2Python_axi4_stream");
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
    (void)ThreadSafeEventFactory::newEvent("pySocket.test_req_ack_req");
    (void)ThreadSafeEventFactory::newEvent("pySocket.test2Python_req_ack_req");
    (void)ThreadSafeEventFactory::newEvent("pySocket.dut2Python_req_ack_ack");
    (void)ThreadSafeEventFactory::newEvent("pySocket.test_push_ack_push");
    (void)ThreadSafeEventFactory::newEvent("pySocket.test_pop_ack_pop");
    (void)ThreadSafeEventFactory::newEvent("pySocket.dut2Python_push_ack_push_ack");
    (void)ThreadSafeEventFactory::newEvent("pySocket.dut2Python_pop_ack_pop_ack");
    (void)ThreadSafeEventFactory::newEvent("pySocket.test_notify_ack_notify");
    (void)ThreadSafeEventFactory::newEvent("pySocket.dut2Python_notify_ack_notify_ack");
    (void)ThreadSafeEventFactory::newEvent("pySocket.test_rdy_vld_vld");
    (void)ThreadSafeEventFactory::newEvent("pySocket.dut2Python_rdy_vld_rdy");
    (void)ThreadSafeEventFactory::newEvent("pySocket.test_axi4_stream_axis");
    (void)ThreadSafeEventFactory::newEvent("pySocket.dut2Python_axi4_stream_axis_rdy");

    SC_THREAD(python2SystemCTestComplete);
    SC_THREAD(systemC2PythonTestComplete);
    SC_THREAD(pythonPushPopTestComplete);
    SC_THREAD(pythonNotifyTestComplete);
    SC_THREAD(pythonRdyVldTestComplete);
    SC_THREAD(pythonAxi4StreamTestComplete);
    SC_THREAD(simHeartbeat);
    SC_THREAD(eotStopSim);
}

void pySocketSocket::python2SystemCTestComplete(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController &controller = testController::GetInstance();
    const std::string test_socket = "python2SystemCTest";
    controller.register_test_name(test_socket);
    controller.wait_test(test_socket, sc_time(1, SC_NS));
    auto ev = socketFactory::getPeerClosedEvent(pySocketSocketCatalog::name_test_req_ack);
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
    auto ev = socketFactory::getPeerClosedEvent(pySocketSocketCatalog::name_test2Python_req_ack);
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
    auto ev = socketFactory::getPeerClosedEvent(pySocketSocketCatalog::name_test_push_ack);
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
    auto ev = socketFactory::getPeerClosedEvent(pySocketSocketCatalog::name_test_notify_ack);
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
    auto ev = socketFactory::getPeerClosedEvent(pySocketSocketCatalog::name_test_rdy_vld);
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
    auto ev = socketFactory::getPeerClosedEvent(pySocketSocketCatalog::name_test_axi4_stream);
    if (ev) {
        sc_core::wait(ev->default_event());
    }
    controller.test_complete(test_socket);
    eot.setEndOfTest(true);
}
