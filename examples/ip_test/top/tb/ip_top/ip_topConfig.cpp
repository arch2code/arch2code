// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=tbConfig --section=prerequisites
#include <string>
#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "ipVariantConfig.h"
#include "srcVariantConfig.h"
import a2c.endOfTest;
// GENERATED_CODE_END
// user #includes and imports here
// A plain translation unit, not a module: either may appear here in any order.
#include <cstring>

#include "testController.h"
#include "workerThread.h"
#include "fwModelMain.h"

import ip;
using namespace ip_ns;
// GENERATED_CODE_BEGIN --template=tbConfig --section=class

class ip_topConfig : public testBenchConfigBase
{
public:
    virtual ~ip_topConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "ip_topTestbench", "", "ip_test"); }
public:
// GENERATED_CODE_END

    // A signed parameterizable type must resolve to a signed C++ container, not
    // merely to a correct bit pattern. pack/unpack sign-extend identically into a
    // signed or an unsigned container, so the generated round-trip cannot tell the
    // two apart; only arithmetic on the alias itself can. An all-ones field is -1,
    // so it compares negative and an arithmetic shift right is value preserving,
    // neither of which holds for an unsigned container.
    template<typename Config>
    static void checkSignedParameterizableField(void)
    {
        typename ipSignedParamSt<Config>::_packedSt allOnes;
        memset(&allOnes, 0xFF, sizeof(allOnes));
        ipSignedParamSt<Config> sample;
        sample.unpack(allOnes);
        Q_ASSERT_CTX(sample.offset < 0, "checkSignedParameterizableField",
            "signed parameterizable field did not unpack negative");
        Q_ASSERT_CTX((sample.offset >> 1) == sample.offset, "checkSignedParameterizableField",
            "signed parameterizable field shifted logically instead of arithmetically");
    }

    bool createTestBench(void) override
    {
        ip_test_ns::test_ip_structs::test();
        checkSignedParameterizableField<ip_test_ns::ipTestConfigDefault>();
        checkSignedParameterizableField<ip_test_ns::ipTestConfigMid>();
        checkSignedParameterizableField<ip_test_ns::ipTestConfigMax>();

        testController::GetInstance().set_test_names({
            "test_ip_uIp0_check",
            "test_ip_uIp1_check",
        });

        // Register the firmware worker and run it as a SystemC thread. The worker
        // event must exist before the testbench hierarchy is built, since the
        // common 'cpu' master resolves it while draining the register-access
        // queue. Mirrors the pro gold-standard lmmiDemoConfig.
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
// GENERATED_CODE_BEGIN --template=tbConfig --section=registration
// === Testbench config registration (ip_topConfig) ===
// The config self-registers through an A2C_REGISTRATION_RETAIN static (see
// instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference. Emitted after the class closes so is_default_testbench_v
// sees a complete type, including a user-supplied isDefaultTestBench marker.
void register_ip_topConfig() {
    testBenchConfigFactory::registerTestBenchConfig("ip_top", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<ip_topConfig>());}, is_default_testbench_v<ip_topConfig>);
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ip_topConfig_registered = (register_ip_topConfig(), 0);
} // namespace
// === End testbench config registration ===
// GENERATED_CODE_END
