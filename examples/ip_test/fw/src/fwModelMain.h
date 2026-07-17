#ifndef FW_MODEL_MAIN_H
#define FW_MODEL_MAIN_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "workerThread.h"
#include "fwIpMain.h"

// Root-owned firmware worker for the ip_test top. Mirrors the pro gold-standard
// lmmiDemo fwModelMain: a workerBase subclass whose startupInit() sequences the
// test phases through the testController, runs the firmware register program
// (fwCheckUIp0 / fwCheckUIp1 over the BSP regRdWr transport driven by the common
// 'cpu' block), and drives end-of-test. The orchestration that previously lived
// in the ip_test-local cpu model threads now lives here so that the 'cpu' block
// can be a generic, common-owned APB master.
class fwModelMain : public workerBase
{
public:
    fwModelMain(void) : workerBase("FW") {}
    bool workAvailable(void) override { return false; }
    void doWork(void) override {}
    void startupInit(void) override;
    void shutdown(void) override {}
};

#endif // FW_MODEL_MAIN_H
