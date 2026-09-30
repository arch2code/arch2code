//

// GENERATED_CODE_PARAM --block=axiSocketMaster_tb --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "axi_read_channel.h"
#include "axi_write_channel.h"
// GENERATED_CODE_END
// user #includes here
#include "socketSync.h"
#include "testController.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module axiSocketMaster_tb.block;
import axiSocketMaster_tb.base;
import axiSocketMaster_tb;
import axiSocketMaster_axiSocket.base;
import axiSocketMaster_consumer.base;
// GENERATED_CODE_END
// user imports here
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace axiSocketMaster_tb_ns;
export SC_MODULE(axiSocketMaster_tb), public blockBase, public axiSocketMaster_tbBase
{
private:

public:
    // channels
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd0_0;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr0_0;
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd0_1;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr0_1;

    //instances contained in block
    std::shared_ptr<axiSocketBase> u_axiSocket0;
    std::shared_ptr<consumerBase> u_consumer0;
    std::shared_ptr<axiSocketBase> u_axiSocket1;
    std::shared_ptr<consumerBase> u_consumer1;

    axiSocketMaster_tb(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiSocketMaster_tb() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Both shells share one lockstep link and one end of test, so the
    // testbench top runs these once rather than each shell.
    void simTimeAdvance(void);
    void eotStopSim(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(axiSocketMaster_tb);

// === Block factory registration (axiSocketMaster_tb) ===
void register_axiSocketMaster_tb_variants() {
    instanceFactory::registerBlock("axiSocketMaster_tb_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axiSocketMaster_tb>(blockName, variant, bbMode)); }, "", "axiSocketMaster");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _axiSocketMaster_tb_registered = (register_axiSocketMaster_tb_variants(), 0);
} // namespace
// === End block factory registration ===

axiSocketMaster_tb::axiSocketMaster_tb(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axiSocketMaster_tb", name(), bbMode)
        ,axiSocketMaster_tbBase(name(), variant)
        ,axiRd0_0("consumer_axiRd0_0", "axiSocket", "api_list_size", 256, "")
        ,axiWr0_0("consumer_axiWr0_0", "axiSocket", "api_list_size", 256, "")
        ,axiRd0_1("consumer_axiRd0_1", "axiSocket", "api_list_size", 256, "")
        ,axiWr0_1("consumer_axiWr0_1", "axiSocket", "api_list_size", 256, "")
        ,u_axiSocket0(std::dynamic_pointer_cast<axiSocketBase>(instanceFactory::createInstance(name(), "u_axiSocket0", "axiSocket", "", "axiSocketMaster")))
        ,u_consumer0(std::dynamic_pointer_cast<consumerBase>(instanceFactory::createInstance(name(), "u_consumer0", "consumer", "", "axiSocketMaster")))
        ,u_axiSocket1(std::dynamic_pointer_cast<axiSocketBase>(instanceFactory::createInstance(name(), "u_axiSocket1", "axiSocket", "", "axiSocketMaster")))
        ,u_consumer1(std::dynamic_pointer_cast<consumerBase>(instanceFactory::createInstance(name(), "u_consumer1", "consumer", "", "axiSocketMaster")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    u_axiSocket0->axiRd0(axiRd0_0);
    u_consumer0->axiRd0(axiRd0_0);
    u_axiSocket0->axiWr0(axiWr0_0);
    u_consumer0->axiWr0(axiWr0_0);
    u_axiSocket1->axiRd0(axiRd0_1);
    u_consumer1->axiRd0(axiRd0_1);
    u_axiSocket1->axiWr0(axiWr0_1);
    u_consumer1->axiWr0(axiWr0_1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(simTimeAdvance);
    SC_THREAD(eotStopSim);
};

void axiSocketMaster_tb::simTimeAdvance(void)
{
    socketSyncQuantumThread();
}

void axiSocketMaster_tb::eotStopSim(void)
{
    testController::GetInstance().wait_all_tests_complete();
    endOfTestState &eot = endOfTestState::GetInstance();
    while (!eot.isEndOfTest()) {
        wait(eot.eotEvent);
    }
    sc_stop();
}

