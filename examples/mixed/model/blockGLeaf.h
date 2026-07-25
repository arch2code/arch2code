#ifndef BLOCKGLEAF_H
#define BLOCKGLEAF_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockGLeaf
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import blockGLeaf.base;
#include "status_channel.h"
import mixed;
using namespace mixed_ns;

SC_MODULE(blockGLeaf), public blockBase, public blockGLeafBase
{
private:

public:

    blockGLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockGLeaf() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void checkForwardedReg(void);

};

#endif //BLOCKGLEAF_H
