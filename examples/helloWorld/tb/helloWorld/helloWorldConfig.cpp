// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <string>

#include "testController.h"
#include "tracker.h"
#include "tagTrackers.h"
#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"

std::string cmdidPrt(int cmdid)
{
    std::stringstream ss;
    ss << "cmd:0x" << std::hex << std::setw(2) << std::setfill('0') << cmdid;
    return(ss.str());
}
std::string tagPrt(int tag)
{
    std::stringstream ss;
    ss << "tag:0x" << std::hex << std::setw(2) << std::setfill('0') << tag;
    return(ss.str());
}

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
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        logging &log = logging::GetInstance();
        log.setDefaultVerbosity(VERBOSITY_HIGH);
        trackerCollection &trackers = trackerCollection::GetInstance();
        trackers.addTracker("cmd", std::make_shared<tracker<simpleString>> (10, "cmd", "C#", cmdidPrt));
        trackers.addTracker("tag", std::make_shared<tracker<tagInfo>>(10, "tag", "T#", tagPrt));
        testController &controller = testController::GetInstance();
        controller.set_test_names({ 
            // all tests should be listed here
            "test_rdy_vld",
            "test_req_ack",
            "test_push_ack",
            "test_pop_ack"
            });
        //create hierarchy
        instanceFactory::registerInstance("helloWorld.uProducer", "model");
        instanceFactory::registerInstance("helloWorld.uConsumer", "model");
        instanceFactory::registerInstance("helloWorld", "model");
        std::shared_ptr<blockBase> tb = instanceFactory::createInstance("", "tb", "helloWorldTestbench", "");
        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        testController &controller = testController::GetInstance();
        Q_ASSERT_CTX(controller.are_all_tests_complete(), "final", "Tests not complete");
        // Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        errorCode::pass();
    }

};
helloWorldConfig::registerTestBenchConfig helloWorldConfig::registerTestBenchConfig_; //register the testBench with the factory
