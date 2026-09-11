// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
import a2c.endOfTest;
#include "testController.h"

// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=tbConfig

class helloWorldConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("helloWorld", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<helloWorldConfig>());}, is_default_testbench_v<helloWorldConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~helloWorldConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "helloWorldTestbench", "", "helloWorld"); }
public:
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        // Seed the testController with the full list of self-driving tests.
        // The producer/consumer model threads register against these names and
        // the testController sequences them. Must run before sc_start().
        testController &controller = testController::GetInstance();
        controller.set_test_names({
            "test_rdy_vld",
            "test_req_ack",
            "test_push_ack",
            "test_pop_ack",
            "test_rdy_vld_arb"
        });

        //create hierarchy
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
helloWorldConfig::registerTestBenchConfig helloWorldConfig::registerTestBenchConfig_; //register the testBench with the factory
