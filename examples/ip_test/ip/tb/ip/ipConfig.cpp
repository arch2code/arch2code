// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"

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
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "ipTestbench", "", "ip"); }
public:
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        //create hierarchy
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
ipConfig::registerTestBenchConfig ipConfig::registerTestBenchConfig_; //register the testBench with the factory
