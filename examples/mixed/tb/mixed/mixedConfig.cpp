// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"
#include "workerThread.h"
#include "testController.h"

import mixed;

// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=tbConfig

class mixedConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("mixed", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<mixedConfig>());}, is_default_testbench_v<mixedConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~mixedConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "mixedTestbench", "", "mixed"); }
public:
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        mixed_test_ns::test_mixed_structs::test();

        testController &controller = testController::GetInstance();
        controller.set_test_names({
            "test_mem_hier_blockd_write",
            "test_mem_hier_blockd_read",
            "test_mem_hier_cpu_read",
            "test_mem_hier_cpu_write",
            "test_mem_hier_cpu_ext_rw",
            "test_mem_local_cpu_rw",
            "test_mem_37bit_cpu_rw",
            "test_reg_cpu_rwg"
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
mixedConfig::registerTestBenchConfig mixedConfig::registerTestBenchConfig_; //register the testBench with the factory

