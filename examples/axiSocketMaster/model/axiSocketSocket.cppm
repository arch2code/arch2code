//

// GENERATED_CODE_PARAM --block=axiSocket
// GENERATED_CODE_BEGIN --template=socket --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "axi_read_port_socket.h"
#include "axi_write_port_socket.h"
#include "axiSocketSocketCatalog.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include <format>
#include "asyncEvent.h"
#include "socketFactory.h"
#include "socketSync.h"
#include "testController.h"
// GENERATED_CODE_BEGIN --template=socket --section=moduleExport
export module axiSocketMaster_axiSocket.socket;
import axiSocketMaster_axiSocket.base;
import axiSocketMaster_tb;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=socket --section=socket
export SC_MODULE(axiSocketSocket), public blockBase, public axiSocketBase
{
public:

    axiSocketSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiSocketSocket() override = default;

private:
    void axiRd0Socket(void);
    void axiWr0Socket(void);

// GENERATED_CODE_END
    // socket shell members
    void axiSocketMasterTestComplete(void);
};

// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
SC_HAS_PROCESS(axiSocketSocket);

// === Socket shell factory registration (axiSocketSocket) ===
void register_axiSocketSocket() {
    instanceFactory::registerBlock("axiSocket_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axiSocketSocket>(blockName, variant, bbMode)); }, "", "axiSocketMaster");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _axiSocketSocket_registered = (register_axiSocketSocket(), 0);
} // namespace
// === End socket shell factory registration ===

void axiSocketSocket::axiRd0Socket(void) {
    Q_ASSERT(socketFactory::getPort(axiSocketSocketCatalog::name_axiRd0(this->name())) != 0,
             "socket " + axiSocketSocketCatalog::name_axiRd0(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(axiRd0, axiSocketSocketCatalog::name_axiRd0(this->name()));
}

void axiSocketSocket::axiWr0Socket(void) {
    Q_ASSERT(socketFactory::getPort(axiSocketSocketCatalog::name_axiWr0(this->name())) != 0,
             "socket " + axiSocketSocketCatalog::name_axiWr0(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(axiWr0, axiSocketSocketCatalog::name_axiWr0(this->name()));
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
    (void)ThreadSafeEventFactory::newEvent((axiSocketSocketCatalog::name_axiRd0(name()) + "_axi_rd_req").c_str());
    (void)ThreadSafeEventFactory::newEvent((axiSocketSocketCatalog::name_axiRd0(name()) + "_axi_rd_boundary").c_str());
    (void)ThreadSafeEventFactory::newEvent((axiSocketSocketCatalog::name_axiWr0(name()) + "_axi_wr_req").c_str());
    (void)ThreadSafeEventFactory::newEvent((axiSocketSocketCatalog::name_axiWr0(name()) + "_axi_wr_boundary").c_str());

    SC_THREAD(axiSocketMasterTestComplete);
}
// user method definitions here

void axiSocketSocket::axiSocketMasterTestComplete(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController &controller = testController::GetInstance();
    const std::string test_socket = "axiSocketMasterTest";
    controller.register_test_name(test_socket);
    controller.wait_test(test_socket, sc_time(1, SC_NS));
    // Python owns stimulus and sends MSG_SHUTDOWN when finished; wait for close.
    for (const std::string &ifc : {
             axiSocketSocketCatalog::name_axiRd0(name()),
             axiSocketSocketCatalog::name_axiWr0(name()),
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
