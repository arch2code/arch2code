//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nested --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
#include "testController.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module nested.block;
import nested.base;
import nested;
import nested_testContainer.base;
import nested_nestedL1.base;
// GENERATED_CODE_END
// user imports here
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace nested_ns;
export SC_MODULE(nested), public blockBase, public nestedBase
{
private:

public:
    // channels
    // Test interface
    rdy_vld_channel< test_st > test;

    //instances contained in block
    std::shared_ptr<testContainerBase> uTestTop;
    std::shared_ptr<nestedL1Base> uNestedL1;

    nested(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nested() override = default;

    // GENERATED_CODE_END
    // block implementation members

    // Bridges testController completion to the end-of-test voting mechanism.
    void doneTest(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(nested);

// === Block factory registration (nested) ===
void register_nested_variants() {
    instanceFactory::registerBlock("nested_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<nested>(blockName, variant, bbMode)); }, "", "nested");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _nested_registered = (register_nested_variants(), 0);
} // namespace
// === End block factory registration ===

nested::nested(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nested", name(), bbMode)
        ,nestedBase(name(), variant)
        ,test("nestedL1_test", "testContainer")
        ,uTestTop(std::dynamic_pointer_cast<testContainerBase>(instanceFactory::createInstance(name(), "uTestTop", "testContainer", "", "nested")))
        ,uNestedL1(std::dynamic_pointer_cast<nestedL1Base>(instanceFactory::createInstance(name(), "uNestedL1", "nestedL1", "", "nested")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uTestTop->test(test);
    uNestedL1->nested1(test);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(doneTest);
};

// End-of-test bridge: the model is self-driving via testController. Wait for all
// registered tests to complete, then vote end-of-test so nestedExternal::eotThread
// can sc_stop() the simulation.
void nested::doneTest(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}

