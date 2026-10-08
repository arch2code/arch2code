#ifndef FW_MODEL_MAIN_H
#define FW_MODEL_MAIN_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "workerThread.h"
#include "fwSimpleMain.h"

// Root-owned firmware worker for the simple_ip top. A workerBase subclass whose
// startupInit() sequences the single test phase through the testController, runs
// the firmware register program (fwCheckUIp over the BSP regRdWr transport
// driven by the common 'cpu' block), and drives end-of-test.
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
