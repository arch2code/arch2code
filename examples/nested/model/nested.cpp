//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "endOfTest.h"
#include "testController.h"

// GENERATED_CODE_PARAM --block=nested
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "nested.h"
#include "testContainerBase.h"
#include "nestedL1Base.h"
SC_HAS_PROCESS(nested);

// === Block factory registration (nested) ===
void force_link_nested() {}

void register_nested_variants() {
    instanceFactory::registerBlock("nested_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<nested>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _nested_registered = (register_nested_variants(), 0);
} // namespace
// === End block factory registration ===

nested::nested(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nested", name(), bbMode)
        ,nestedBase(name(), variant)
        ,test("nestedL1_test", "testContainer")
        ,uTestTop(std::dynamic_pointer_cast<testContainerBase>((force_link_testContainer(), instanceFactory::createInstance(name(), "uTestTop", "testContainer", ""))))
        ,uNestedL1(std::dynamic_pointer_cast<nestedL1Base>((force_link_nestedL1(), instanceFactory::createInstance(name(), "uNestedL1", "nestedL1", ""))))
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

