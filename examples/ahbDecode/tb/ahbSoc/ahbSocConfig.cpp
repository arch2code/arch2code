// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ahbSoc
// GENERATED_CODE_BEGIN --template=tbConfig --section=prerequisites
#include <string>
#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
import a2c.endOfTest;
// GENERATED_CODE_END
// user #includes and imports here
// A plain translation unit, not a module: either may appear here in any order.
// Required by the createTestBench() and final() bodies below, which seed and
// assert on test-completion state.
#include "testController.h"
// GENERATED_CODE_BEGIN --template=tbConfig --section=class

class ahbSocConfig : public testBenchConfigBase
{
public:
    virtual ~ahbSocConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "ahbSocTestbench", "", "ahbDecode"); }
public:
// GENERATED_CODE_END

    // errorResponses is 1 while project.yaml sets fileGeneration
    // regBusErrorResponses, and --param errorResponses,0 runs a build
    // generated without it.
    ahbSocConfig() { addParam("errorResponses", 1); }

    bool createTestBench(void) override
    {
        testController &controller = testController::GetInstance();
        controller.set_test_names({
            "test_ahbDecode"
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
// === Testbench config registration (ahbSocConfig) ===
// The config self-registers through an A2C_REGISTRATION_RETAIN static (see
// instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference. Emitted after the class closes so is_default_testbench_v
// sees a complete type, including a user-supplied isDefaultTestBench marker.
void register_ahbSocConfig() {
    testBenchConfigFactory::registerTestBenchConfig("ahbSoc", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<ahbSocConfig>());}, is_default_testbench_v<ahbSocConfig>);
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ahbSocConfig_registered = (register_ahbSocConfig(), 0);
} // namespace
// === End testbench config registration ===
// GENERATED_CODE_END
