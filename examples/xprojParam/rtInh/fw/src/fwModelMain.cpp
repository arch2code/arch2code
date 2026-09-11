// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "fwModelMain.h"
#include "testController.h"
import a2c.endOfTest;
#include "q_assert.h"

void fwModelMain::startupInit(void)
{
    testController &controller = testController::GetInstance();

    // This worker is the sole end-of-test voter. Register before signalling.
    endOfTest eot(true);

    // Single phase: uLeaf register check through both routers. The phase
    // order is seeded by the testbench config's set_test_names(); wait_test
    // blocks until it is this phase's turn.
    controller.register_test_name("test_xpRtInh_uLeaf_check");
    controller.wait_test("test_xpRtInh_uLeaf_check");
    Q_ASSERT_CTX(fw_ns::fwCheckULeaf(), "fwModelMain", "uLeaf firmware register check failed");
    controller.test_complete("test_xpRtInh_uLeaf_check");

    // Firmware phase done; signal end of test.
    eot.setEndOfTest(true);
}
