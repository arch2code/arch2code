// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dut --variant=dutV0
// GENERATED_CODE_BEGIN --template=tbConfig --section=prerequisites
#include <string>
#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "xifVariantConfig.h"
import a2c.endOfTest;
// GENERATED_CODE_END
// user #includes and imports here
// A plain translation unit, not a module: either may appear here in any order.
#include "testController.h"
// GENERATED_CODE_BEGIN --template=tbConfig --section=class

class dutConfig : public testBenchConfigBase
{
public:
    virtual ~dutConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "dutTestbench", "", "xif"); }
public:
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        // Seed the testController with the self-driving test the src and sink
        // model threads register against. Must run before sc_start().
        testController::GetInstance().set_test_names({ "test_stream" });

        // The testbench top self-registers via an A2C_REGISTRATION_RETAIN
        // static in dutTestbench.cpp (see instanceFactory.h),
        // reachable through direct-.o linking with no force-link reference.
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
// === Testbench config registration (dutConfig) ===
// The config self-registers through an A2C_REGISTRATION_RETAIN static (see
// instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference. Emitted after the class closes so is_default_testbench_v
// sees a complete type, including a user-supplied isDefaultTestBench marker.
void register_dutConfig() {
    testBenchConfigFactory::registerTestBenchConfig("dut", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<dutConfig>());}, is_default_testbench_v<dutConfig>);
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _dutConfig_registered = (register_dutConfig(), 0);
} // namespace
// === End testbench config registration ===
// GENERATED_CODE_END
