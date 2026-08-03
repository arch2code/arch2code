// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "fwModelMain.h"
#include "testController.h"
import a2c.endOfTest;
#include "q_assert.h"

void fwModelMain::startupInit(void)
{
    testController &controller = testController::GetInstance();

    // This worker is the sole end-of-test voter (the orchestration moved here
    // from the retired ip_test-local cpu model). Register before signalling.
    endOfTest eot(true);

    // Phase 1: uIp0 register check. The phase order is seeded by the testbench
    // config's set_test_names(); wait_test blocks until it is this phase's turn.
    controller.register_test_name("test_ip_uIp0_check");
    controller.wait_test("test_ip_uIp0_check");
    // Allow time for src (model or RTL) to push and ip to capture before reading.
    event->waitnsec(50);
    Q_ASSERT_CTX(fw_ns::fwCheckUIp0(), "fwModelMain", "uIp0 firmware register check failed");
    controller.test_complete("test_ip_uIp0_check");

    // Phase 2: uIp1 register check.
    controller.register_test_name("test_ip_uIp1_check");
    controller.wait_test("test_ip_uIp1_check");
    event->waitnsec(50);
    Q_ASSERT_CTX(fw_ns::fwCheckUIp1(), "fwModelMain", "uIp1 firmware register check failed");
    controller.test_complete("test_ip_uIp1_check");

    // All firmware phases done; signal end of test.
    eot.setEndOfTest(true);
}
