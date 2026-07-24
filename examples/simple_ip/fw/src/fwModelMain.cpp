// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "fwModelMain.h"
#include "testController.h"
#include "endOfTest.h"
#include "q_assert.h"

void fwModelMain::startupInit(void)
{
    testController &controller = testController::GetInstance();

    // This worker is the sole end-of-test voter. Register before signalling.
    endOfTest eot(true);

    // Single phase: uIp register check. The phase order is seeded by the
    // testbench config's set_test_names(); wait_test blocks until it is this
    // phase's turn.
    controller.register_test_name("test_ip_uIp_check");
    controller.wait_test("test_ip_uIp_check");
    // Allow time for dataGen to push and ip to capture before reading.
    event->waitnsec(50);
    Q_ASSERT_CTX(fw_ns::fwCheckUIp(), "fwModelMain", "uIp firmware register check failed");
    controller.test_complete("test_ip_uIp_check");

    // Firmware phase done; signal end of test.
    eot.setEndOfTest(true);
}
