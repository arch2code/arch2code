// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtInhTop
// GENERATED_CODE_BEGIN --template=tbConfig --section=prerequisites
#include <string>
#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
import a2c.endOfTest;
// GENERATED_CODE_END
// user #includes and imports here
// A plain translation unit, not a module: either may appear here in any order.
#include "testController.h"
#include "workerThread.h"
#include "fwModelMain.h"
// GENERATED_CODE_BEGIN --template=tbConfig --section=class

class xpRtInhTopConfig : public testBenchConfigBase
{
public:
    virtual ~xpRtInhTopConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "xpRtInhTopTestbench", "", "xpRtInh"); }
public:
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        testController::GetInstance().set_test_names({
            "test_xpRtInh_uLeaf_check",
        });

        // Register the firmware worker and run it as a SystemC thread. The worker
        // event must exist before the testbench hierarchy is built, since the
        // common 'cpu' master resolves it while draining the register-access
        // queue.
        workerFactory::addWorker({
            { "fw", std::make_shared<fwModelMain>() }
        });
        workerFactory::setNumThreads(0, true);
        workerFactory::assignWorkersToThreads();
        workerFactory::startCPUThreads();

        //create hierarchy
        std::shared_ptr<blockBase> tb = createTbTop();
        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        workerFactory::joinCPUThreads();
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        Q_ASSERT_CTX(testController::GetInstance().are_all_tests_complete(), "final", "Not all tests completed");
        errorCode::pass();
    }

};
// GENERATED_CODE_BEGIN --template=tbConfig --section=registration
// === Testbench config registration (xpRtInhTopConfig) ===
// The config self-registers through an A2C_REGISTRATION_RETAIN static (see
// instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference. Emitted after the class closes so is_default_testbench_v
// sees a complete type, including a user-supplied isDefaultTestBench marker.
void register_xpRtInhTopConfig() {
    testBenchConfigFactory::registerTestBenchConfig("xpRtInhTop", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<xpRtInhTopConfig>());}, is_default_testbench_v<xpRtInhTopConfig>);
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpRtInhTopConfig_registered = (register_xpRtInhTopConfig(), 0);
} // namespace
// === End testbench config registration ===
// GENERATED_CODE_END
