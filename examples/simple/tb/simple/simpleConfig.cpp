// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"
#include "testController.h"

// Forward declaration of the active force-link function emitted by
// the testbench class. Calling it from createTestBench() creates a
// real symbol reference into simpleTestbench.cpp so the
// linker pulls that TU into the program even when nothing else
// references its symbols. This is required under C++20 modules and
// static-archive linking.
void force_link_simpleTestbench();

// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=tbConfig

class simpleConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("simple", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<simpleConfig>());}, is_default_testbench_v<simpleConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~simpleConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        // Seed the testController with the full list of self-driving tests.
        // The DUT's producer/consumer model threads register against these
        // names and the testController sequences them. Must run before sc_start().
        testController &controller = testController::GetInstance();
        controller.set_test_names({
            "test_tag0",
            "test_tag1"
        });

        //create hierarchy
        force_link_simpleTestbench();
        std::shared_ptr<blockBase> tb = instanceFactory::createInstance("", "tb", "simpleTestbench", "");
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
simpleConfig::registerTestBenchConfig simpleConfig::registerTestBenchConfig_; //register the testBench with the factory
