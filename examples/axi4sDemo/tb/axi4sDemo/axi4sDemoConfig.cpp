// 

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"

// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=tbConfig

class axi4sDemoConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("axi4sDemo", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<axi4sDemoConfig>());}, is_default_testbench_v<axi4sDemoConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~axi4sDemoConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        //create hierarchy
        std::shared_ptr<blockBase> tb = instanceFactory::createInstance("", "tb", "axi4sDemoTestbench", "");
        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        errorCode::pass();
    }

};
axi4sDemoConfig::registerTestBenchConfig axi4sDemoConfig::registerTestBenchConfig_; //register the testBench with the factory
