// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
// Required by the final() body below, which asserts on end-of-test state.
import a2c.endOfTest;

// GENERATED_CODE_PARAM --block=twoClk
// GENERATED_CODE_BEGIN --template=tbConfig

class twoClkConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("twoClk", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<twoClkConfig>());}, is_default_testbench_v<twoClkConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
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
        // The testbench top self-registers via an A2C_REGISTRATION_RETAIN
        // static in twoClkTestbench.cpp (see instanceFactory.h),
        // reachable through direct-.o linking with no force-link reference.
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
twoClkConfig::registerTestBenchConfig twoClkConfig::registerTestBenchConfig_; //register the testBench with the factory
