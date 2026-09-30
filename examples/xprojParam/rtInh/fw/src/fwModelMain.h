#ifndef FW_MODEL_MAIN_H
#define FW_MODEL_MAIN_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "workerThread.h"
#include "fwXpRtInhMain.h"

// Firmware worker: runs fwCheckULeaf as the single test phase and votes end of test.
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
