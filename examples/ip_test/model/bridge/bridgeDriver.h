#ifndef BRIDGEDRIVER_H
#define BRIDGEDRIVER_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=bridgeDriver
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "bridgeDriverBase.h"

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
};

#endif //BRIDGEDRIVER_H
