// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"
#include "testController.h"

// Forward declaration of the active force-link function emitted by
// the testbench class. Calling it from createTestBench() creates a
// real symbol reference into axiDemoTestbench.cpp so the
// linker pulls that TU into the program even when nothing else
// references its symbols. This is required under C++20 modules and
// static-archive linking.
void force_link_axiDemoTestbench();

// GENERATED_CODE_PARAM --block=axiDemo
// GENERATED_CODE_BEGIN --template=tbConfig

class axiDemoConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("axiDemo", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<axiDemoConfig>());}, is_default_testbench_v<axiDemoConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~axiDemoConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        // Seed the testController with the full list of self-driving tests.
        // The producer/consumer model threads register against these names and
        // the testController sequences them. Must run before sc_start().
        testController &controller = testController::GetInstance();
        controller.set_test_names({
            "test_axird0",
            "test_axird1",
            "test_axiwr0",
            "test_axiwr1",
            "test_axiwr2",
            "test_axiwr3"
        });

        //create hierarchy
        force_link_axiDemoTestbench();
        std::shared_ptr<blockBase> tb = instanceFactory::createInstance("", "tb", "axiDemoTestbench", "");
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
axiDemoConfig::registerTestBenchConfig axiDemoConfig::registerTestBenchConfig_; //register the testBench with the factory
