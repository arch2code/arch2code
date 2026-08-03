// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
import a2c.endOfTest;

// GENERATED_CODE_PARAM --block=core
// GENERATED_CODE_BEGIN --template=tbConfig

class coreConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("core", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<coreConfig>());}, is_default_testbench_v<coreConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~coreConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        // The testbench top self-registers via an A2C_REGISTRATION_RETAIN
        // static in coreTestbench.cpp (see instanceFactory.h),
        // reachable through direct-.o linking with no force-link reference.
        std::shared_ptr<blockBase> tb = instanceFactory::createInstance("", "tb", "coreTestbench", "");
        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        errorCode::pass();
    }

};
coreConfig::registerTestBenchConfig coreConfig::registerTestBenchConfig_; //register the testBench with the factory
