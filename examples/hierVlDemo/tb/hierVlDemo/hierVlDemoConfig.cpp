// 

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"

// GENERATED_CODE_PARAM --block=hierVlDemo
// GENERATED_CODE_BEGIN --template=tbConfig

class hierVlDemoConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("hierVlDemo", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<hierVlDemoConfig>());}, is_default_testbench_v<hierVlDemoConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~hierVlDemoConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "hierVlDemoTestbench", "", "hierVlDemo"); }
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
hierVlDemoConfig::registerTestBenchConfig hierVlDemoConfig::registerTestBenchConfig_; //register the testBench with the factory
