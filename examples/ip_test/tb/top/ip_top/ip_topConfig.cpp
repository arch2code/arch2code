// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"
#include "testController.h"
#include "ipConfig.h"

import ip;
using namespace ip_ns;

// Forward declaration of the active force-link function emitted by the
// testbench class. Calling it from createTestBench() creates a real
// symbol reference into ip_topTestbench.cpp so the linker pulls that
// TU into the program. See plan-block-registration.md
// "Force-Link Function".
void force_link_ip_topTestbench();

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=tbConfig

class ip_topConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("ip_top", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<ip_topConfig>());}, is_default_testbench_v<ip_topConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~ip_topConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        test_ip_structs<ipDefaultConfig>::test();

        testController::GetInstance().set_test_names({
            "test_ip_uIp0_check",
            "test_ip_uIp1_check",
        });

        //create hierarchy
        force_link_ip_topTestbench();
        std::shared_ptr<blockBase> tb = instanceFactory::createInstance("", "tb", "ip_topTestbench", "");
        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        errorCode::pass();
    }

};
ip_topConfig::registerTestBenchConfig ip_topConfig::registerTestBenchConfig_; //register the testBench with the factory
