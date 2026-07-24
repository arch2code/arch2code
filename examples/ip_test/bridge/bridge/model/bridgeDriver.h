#ifndef BRIDGEDRIVER_H
#define BRIDGEDRIVER_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "endOfTest.h"

// GENERATED_CODE_PARAM --block=bridgeDriver
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import bridgeDriver.base;
#include "push_ack_channel.h"
import ipBridge;
using namespace ipBridge_ns;

SC_MODULE(bridgeDriver), public blockBase, public bridgeDriverBase
{
private:

public:

    bridgeDriver(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bridgeDriver() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void driveOut8(void);
    void driveOut70(void);
    // One voter per stimulus stream; each votes once its push is acked through
    // the bridge, so the test ends only after both data paths have run.
    endOfTest eotOut8_{true};
    endOfTest eotOut70_{true};
};

#endif //BRIDGEDRIVER_H
