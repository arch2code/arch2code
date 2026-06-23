#ifndef BLOCKA_H
#define BLOCKA_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "blockABase.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
import apbDecode;
using namespace apbDecode_ns;

SC_MODULE(blockA), public blockBase, public blockABase
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:

    //registers
    hwRegister< aRegSt, 8 > roA; // A Read Only register
    hwRegister< un0ARegSt, 8 > rwUn0A; // A unaligned Read Write register
    hwRegister< un0ARegSt, 8 > roUn0A; // A unaligned Read Only register
    hwRegister< un0ARegSt, 8 > extA; // A unaligned Read Only register defined externally

    memories mems;
    //memories
    hwMemory< aMemSt > blockATable0;
    hwMemory< aMemSt > blockATableX;
    hwMemory< aMemSt > blockATable1;

    blockA(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockA() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        blockABase::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

// GENERATED_CODE_END

private:
    void LocalRegAccess();
};

#endif //BLOCKA_H
