import a2c.endOfTest;
// GENERATED_CODE_PARAM --block=axiSocket
#include <format>
#include "asyncEvent.h"
#include "axiSocketSocketCatalog.h"
#include "socketFactory.h"
#include "socketSync.h"
#include "testController.h"
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "axiSocketSocket.h"

SC_HAS_PROCESS(axiSocketSocket);

axiSocketSocket::registerBlock axiSocketSocket::registerBlock_; //register the block with the factory

void axiSocketSocket::axiRd0Socket(void) {
    port_socket(axiRd0, "axiSocket.axiRd0");
}

void axiSocketSocket::axiWr0Socket(void) {
    port_socket(axiWr0, "axiSocket.axiWr0");
}

axiSocketSocket::axiSocketSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axiSocket", name(), bbMode)
        ,axiSocketBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(axiRd0Socket);
    SC_THREAD(axiWr0Socket);

// GENERATED_CODE_END
    (void)ThreadSafeEventFactory::newEvent("axiSocket.axiRd0_axi_rd_req");
    (void)ThreadSafeEventFactory::newEvent("axiSocket.axiRd0_axi_rd_boundary");
    (void)ThreadSafeEventFactory::newEvent("axiSocket.axiWr0_axi_wr_req");
    (void)ThreadSafeEventFactory::newEvent("axiSocket.axiWr0_axi_wr_boundary");

    SC_THREAD(axiSocketMasterTestComplete);
    SC_THREAD(simTimeAdvance);
    SC_THREAD(eotStopSim);
}

void axiSocketSocket::axiSocketMasterTestComplete(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController &controller = testController::GetInstance();
    const std::string test_socket = "axiSocketMasterTest";
    controller.register_test_name(test_socket);
    controller.wait_test(test_socket, sc_time(1, SC_NS));
    // Python owns stimulus and sends MSG_SHUTDOWN when finished; wait for close.
    for (const char *ifc : {
             axiSocketSocketCatalog::name_axiRd0,
             axiSocketSocketCatalog::name_axiWr0,
         }) {
        while (socketFactory::getFd(ifc) >= 0) {
            if (auto ev = socketFactory::getPeerClosedEvent(ifc)) {
                wait(ev->default_event());
            } else if (socketSyncTimeGated()) {
                wait(socketSyncTimeTickEvent());
            } else {
                wait(sc_time(10, SC_US));
            }
        }
    }
    controller.test_complete(test_socket);
    eot.setEndOfTest(true);
}

void axiSocketSocket::simTimeAdvance(void)
{
    socketSyncQuantumThread();
}

void axiSocketSocket::eotStopSim(void)
{
    testController::GetInstance().wait_all_tests_complete();
    endOfTestState &eot = endOfTestState::GetInstance();
    while (!eot.isEndOfTest()) {
        wait(eot.eotEvent);
    }
    sc_stop();
}
