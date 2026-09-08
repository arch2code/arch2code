// 

// GENERATED_CODE_PARAM --block=xpDeparamTop
// GENERATED_CODE_BEGIN --template=tbConfig --section=prerequisites
#include <string>
#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
import a2c.endOfTest;
// GENERATED_CODE_END
// user #includes and imports here
// A plain translation unit, not a module: either may appear here in any order.
// GENERATED_CODE_BEGIN --template=tbConfig --section=class

class xpDeparamTopConfig : public testBenchConfigBase
{
public:
    virtual ~xpDeparamTopConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "xpDeparamTopTestbench", "", "xpDeparam"); }
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
// === Testbench config registration (xpDeparamTopConfig) ===
// The config self-registers through an A2C_REGISTRATION_RETAIN static (see
// instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference. Emitted after the class closes so is_default_testbench_v
// sees a complete type, including a user-supplied isDefaultTestBench marker.
void register_xpDeparamTopConfig() {
    testBenchConfigFactory::registerTestBenchConfig("xpDeparamTop", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<xpDeparamTopConfig>());}, is_default_testbench_v<xpDeparamTopConfig>);
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpDeparamTopConfig_registered = (register_xpDeparamTopConfig(), 0);
} // namespace
// === End testbench config registration ===
// GENERATED_CODE_END
