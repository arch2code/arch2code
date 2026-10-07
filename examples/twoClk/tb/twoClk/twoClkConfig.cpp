// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClk
// GENERATED_CODE_BEGIN --template=tbConfig --section=prerequisites
#include <string>
#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
import a2c.endOfTest;
// GENERATED_CODE_END
// user #includes and imports here
// A plain translation unit, not a module: either may appear here in any order.
#include "systemc.h"
// GENERATED_CODE_BEGIN --template=tbConfig --section=class

class twoClkConfig : public testBenchConfigBase
{
public:
    virtual ~twoClkConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "twoClkTestbench", "", "twoClk"); }
public:
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        // The testbench top self-registers; just call createTbTop().
        std::shared_ptr<blockBase> tb = createTbTop();
        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        errorCode::pass();
    }

};
// GENERATED_CODE_BEGIN --template=tbConfig --section=registration
// === Testbench config registration (twoClkConfig) ===
// The config self-registers through an A2C_REGISTRATION_RETAIN static (see
// instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference. Emitted after the class closes so is_default_testbench_v
// sees a complete type, including a user-supplied isDefaultTestBench marker.
void register_twoClkConfig() {
    testBenchConfigFactory::registerTestBenchConfig("twoClk", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<twoClkConfig>());}, is_default_testbench_v<twoClkConfig>);
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _twoClkConfig_registered = (register_twoClkConfig(), 0);
} // namespace
// === End testbench config registration ===
// GENERATED_CODE_END
