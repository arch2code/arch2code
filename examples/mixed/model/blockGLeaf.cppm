//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockGLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "status_channel.h"
// GENERATED_CODE_END
#include "testController.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module mixed_blockGLeaf.block;
import mixed_blockGLeaf.base;
import mixed;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace mixed_ns;
export SC_MODULE(blockGLeaf), public blockBase, public blockGLeafBase
{
private:

public:

    blockGLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockGLeaf() override = default;

    // GENERATED_CODE_END
    // block implementation members

    void checkForwardedReg(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(blockGLeaf);

// === Block factory registration (blockGLeaf) ===
void register_blockGLeaf_variants() {
    instanceFactory::registerBlock("blockGLeaf_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockGLeaf>(blockName, variant, bbMode)); }, "", "mixed");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _blockGLeaf_registered = (register_blockGLeaf_variants(), 0);
} // namespace
// === End block factory registration ===

blockGLeaf::blockGLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockGLeaf", name(), bbMode)
        ,blockGLeafBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(checkForwardedReg);
};

void blockGLeaf::checkForwardedReg(void)
{
    testController &controller = testController::GetInstance();
    std::string test_rwg = "test_reg_cpu_rwg";
    controller.register_test_name(test_rwg);
    controller.wait_test(test_rwg, sc_core::sc_time(1, sc_core::SC_NS));

    // Block until the parameterized reg-handler forwards rwG over its status
    // channel: proves the whole path APB -> hwRegisterIf handler -> status_out ->
    // this leaf's status_in. read() parks on the update event, so this thread is
    // already waiting before the CPU's multi-cycle APB write drives the value.
    dRegSt v = rwG->read();
    dRegSt::_packedSt packed;
    v.pack(packed);
    if (static_cast<uint32_t>(packed) == 0x5A) {
        log_.logPrint("BlockGLeaf received forwarded rwG value - path verify success", LOG_ALWAYS);
    } else {
        log_.logPrint(std::format("BlockGLeaf forwarded rwG mismatch. Expected 0x5A, got 0x{:x}",
                                  static_cast<uint32_t>(packed)), LOG_ALWAYS);
        errorCode::fail("blockGLeaf did not receive forwarded rwG value");
    }

    controller.test_complete(test_rwg);
}

