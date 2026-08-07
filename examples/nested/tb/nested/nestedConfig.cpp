// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nested
// GENERATED_CODE_BEGIN --template=tbConfig --section=prerequisites
#include <string>
#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
import a2c.endOfTest;
// GENERATED_CODE_END
// user #includes and imports here
// A plain translation unit, not a module: either may appear here in any order.
#include "testController.h"
#include "tracker.h"

// Pretty-printer for the cmdid tracker entries used by the producer/consumer
// data-path tests.
static std::string cmdidPrt(int cmdid)
{
    std::stringstream ss;
    ss << "cmdid:0x" << std::hex << std::setw(3) << std::setfill('0') << cmdid;
    return(ss.str());
}
// GENERATED_CODE_BEGIN --template=tbConfig --section=class

class nestedConfig : public testBenchConfigBase
{
public:
    virtual ~nestedConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "nestedTestbench", "", "nested"); }
public:
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        // The producer data-path tests look up the "cmdid" tracker; register it
        // before the hierarchy is built. Must run before sc_start().
        trackerCollection &trackers = trackerCollection::GetInstance();
        trackers.addTracker("cmdid", std::make_shared<tracker<simpleString>> (10, "cmdid", "C#", cmdidPrt));

        // Seed the testController with the full list of self-driving tests. The
        // block model threads register against these names and the testController
        // sequences them.
        testController &controller = testController::GetInstance();
        controller.set_test_names({
            "test1",
            "test2",
            "src_trans_dest_trans_rv_size",
            "src_clock_dest_trans_rv_size",
            "src_trans_dest_clock_rv_size",
            "src_trans_dest_trans_rv_tracker",
            "src_clock_dest_trans_rv_tracker",
            "src_trans_dest_clock_rv_tracker"
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
// GENERATED_CODE_BEGIN --template=tbConfig --section=registration
// === Testbench config registration (nestedConfig) ===
// The config self-registers through an A2C_REGISTRATION_RETAIN static (see
// instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference. Emitted after the class closes so is_default_testbench_v
// sees a complete type, including a user-supplied isDefaultTestBench marker.
void register_nestedConfig() {
    testBenchConfigFactory::registerTestBenchConfig("nested", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<nestedConfig>());}, is_default_testbench_v<nestedConfig>);
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _nestedConfig_registered = (register_nestedConfig(), 0);
} // namespace
// === End testbench config registration ===
// GENERATED_CODE_END
