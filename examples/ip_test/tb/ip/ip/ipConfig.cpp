// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"

// Forward declaration of the active force-link function emitted by
// the testbench class. See plan-block-registration.md
// "Force-Link Function".
void force_link_ipTestbench();

// GENERATED_CODE_PARAM --block=ip --variant=variant0
// GENERATED_CODE_BEGIN --template=tbConfig

class ipConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("ip", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<ipConfig>());}, is_default_testbench_v<ipConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~ipConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        //create hierarchy
        force_link_ipTestbench();
        std::shared_ptr<blockBase> tb = instanceFactory::createInstance("", "tb", "ipTestbench", "");
        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        errorCode::pass();
    }

};
ipConfig::registerTestBenchConfig ipConfig::registerTestBenchConfig_; //register the testBench with the factory
