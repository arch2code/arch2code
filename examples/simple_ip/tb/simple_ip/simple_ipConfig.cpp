// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"
#include "testController.h"
#include "workerThread.h"
#include "fwModelMain.h"

// GENERATED_CODE_PARAM --block=simple_ip
// GENERATED_CODE_BEGIN --template=tbConfig

class simple_ipConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("simple_ip", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<simple_ipConfig>());}, is_default_testbench_v<simple_ipConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~simple_ipConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "simple_ipTestbench", "", "simple_ip"); }
public:
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        testController::GetInstance().set_test_names({
            "test_ip_uIp_check",
        });

        // Register the firmware worker and run it as a SystemC thread. The worker
        // event must exist before the testbench hierarchy is built, since the
        // common 'cpu' master resolves it while draining the register-access
        // queue.
        workerFactory::addWorker({
            { "fw", std::make_shared<fwModelMain>() }
        });
        workerFactory::setNumThreads(0, true);
        workerFactory::assignWorkersToThreads();
        workerFactory::startCPUThreads();

        //create hierarchy
        std::shared_ptr<blockBase> tb = createTbTop();
        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        workerFactory::joinCPUThreads();
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        Q_ASSERT_CTX(testController::GetInstance().are_all_tests_complete(), "final", "Not all tests completed");
        errorCode::pass();
    }

};
simple_ipConfig::registerTestBenchConfig simple_ipConfig::registerTestBenchConfig_; //register the testBench with the factory
