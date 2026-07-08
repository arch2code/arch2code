#ifndef BLOCKB_H
#define BLOCKB_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import blockB.base;
#include "apb_channel.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
import apbDecode;
using namespace apbDecode_ns;

SC_MODULE(blockB), public blockBase, public blockBBase
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:

    //registers
    hwRegister< un0BRegSt, 4 > rwUn0B; // A unaligned four bytes Read Write register
    hwRegister< aSizeRegSt, 4 > roB; // A Read Only register

    memories mems;
    //memories
    hwMemory< bMemSt > blockBTable;

    blockB(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockB() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        blockBBase::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END

};

#endif //BLOCKB_H
