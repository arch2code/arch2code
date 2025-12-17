// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"

// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=tbConfig

class mixedConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("mixed", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<mixedConfig>());}, is_default_testbench_v<mixedConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~mixedConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        //create hierarchy
        std::shared_ptr<blockBase> tb = instanceFactory::createInstance("", "tb", "mixedTestbench", "");
        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        errorCode::pass();
    }

};
mixedConfig::registerTestBenchConfig mixedConfig::registerTestBenchConfig_; //register the testBench with the factory

