// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
// Required by the final() body below, which asserts on end-of-test and
// test-completion state.
import a2c.endOfTest;
#include "testController.h"

// GENERATED_CODE_PARAM --block=clkGen
// GENERATED_CODE_BEGIN --template=tbConfig

class clkGenConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("clkGen", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<clkGenConfig>());}, is_default_testbench_v<clkGenConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~clkGenConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "clkGenTestbench", "", "clkGen"); }
public:
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        // clkGen has no boundary data ports (only its clock/reset boundary),
        // so there is nothing for the External to drive and no BFM to check
        // a transfer against: the run window itself, closed by the
        // External's stimulusThread once it has elapsed, is the one test.
        testController &controller = testController::GetInstance();
        controller.set_test_names({
            "clkGenRunWindow"
        });

        // The testbench top self-registers via an A2C_REGISTRATION_RETAIN
        // static in clkGenTestbench.cpp (see instanceFactory.h),
        // reachable through direct-.o linking with no force-link reference.
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
clkGenConfig::registerTestBenchConfig clkGenConfig::registerTestBenchConfig_; //register the testBench with the factory
