// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseChain --variant=v8
// GENERATED_CODE_BEGIN --template=tbConfig --section=prerequisites
#include <string>
#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
import uvmReuse.uvmReuseChain.config;
import a2c.endOfTest;
// GENERATED_CODE_END
// user #includes and imports here
// A plain translation unit, not a module: either may appear here in any order.
// Required by the createTestBench() and final() bodies below, which seed and
// assert on test-completion state.
#include "testController.h"
// GENERATED_CODE_BEGIN --template=tbConfig --section=class

class uvmReuseChainConfig : public testBenchConfigBase
{
public:
    virtual ~uvmReuseChainConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "uvmReuseChainTestbench", "", "uvmReuse"); }
public:
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        // uDrv programs both leaf offsets, then streams the frames that uSink
        // checks; final() fails until both have completed.
        testController &controller = testController::GetInstance();
        controller.set_test_names({
            "program_test", "stream_test"
        });

        // The testbench top self-registers; just call createTbTop().
        std::shared_ptr<blockBase> tb = createTbTop();
        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        Q_ASSERT_CTX(testController::GetInstance().are_all_tests_complete(), "final", "Not all tests completed");
        errorCode::pass();
    }

};
// GENERATED_CODE_BEGIN --template=tbConfig --section=registration
// === Testbench config registration (uvmReuseChainConfig) ===
// The config self-registers through an A2C_REGISTRATION_RETAIN static (see
// instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference. Emitted after the class closes so is_default_testbench_v
// sees a complete type, including a user-supplied isDefaultTestBench marker.
void register_uvmReuseChainConfig() {
    testBenchConfigFactory::registerTestBenchConfig("uvmReuseChain", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<uvmReuseChainConfig>());}, is_default_testbench_v<uvmReuseChainConfig>);
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmReuseChainConfig_registered = (register_uvmReuseChainConfig(), 0);
} // namespace
// === End testbench config registration ===
// GENERATED_CODE_END
