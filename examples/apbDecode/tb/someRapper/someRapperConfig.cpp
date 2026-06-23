// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"
#include "testController.h"

// Forward declaration of the active force-link function emitted by
// the testbench class. Calling it from createTestBench() creates a
// real symbol reference into someRapperTestbench.cpp so the
// linker pulls that TU into the program even when nothing else
// references its symbols. This is required under C++20 modules and
// static-archive linking.
void force_link_someRapperTestbench();

// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=tbConfig

class someRapperConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("someRapper", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<someRapperConfig>());}, is_default_testbench_v<someRapperConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~someRapperConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        // Seed the testController with the self-driving test the cpu model runs.
        // The cpu registers against this name and the testController sequences it.
        // Must run before sc_start().
        testController::GetInstance().set_test_names({
            "test_apbDecode"
        });

        //create hierarchy
        force_link_someRapperTestbench();
        std::shared_ptr<blockBase> tb = instanceFactory::createInstance("", "tb", "someRapperTestbench", "");
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
someRapperConfig::registerTestBenchConfig someRapperConfig::registerTestBenchConfig_; //register the testBench with the factory
