#ifndef BLOCKBREGS_H
#define BLOCKBREGS_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockBRegs
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "blockBRegsBase.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
import mixed;
using namespace mixed_ns;
import mixedBlockC;
using namespace mixedBlockC_ns;
import mixedInclude;
using namespace mixedInclude_ns;

SC_MODULE(blockBRegs), public blockBase, public blockBRegsBase
{
private:
    void regHandler(void);
    addressMap regs;

public:

    //registers
    hwRegister< dRegSt, 4 > rwD; // A Read Write register
    hwRegister< bSizeRegSt, 4 > roBsize; // A Read Only register with a structure that has a definition from an included context
    hwMemoryPort< bSizeSt, bigSt > blockBTable1_adapter;
    hwMemoryPort< bSizeSt, seeSt > blockBTableExt_adapter;
    hwMemoryPort< bSizeSt, test37BitRegSt > blockBTable37Bit_adapter;

    blockBRegs(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockBRegs() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //BLOCKBREGS_H
