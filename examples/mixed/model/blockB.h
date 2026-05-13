#ifndef BLOCKB_H
#define BLOCKB_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include <vector>

// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "blockBBase.h"
#include "addressMap.h"
#include "hwMemory.h"
#include "mixedConfig.h"
import mixed;
using namespace mixed_ns;
import mixedBlockC;
using namespace mixedBlockC_ns;
import mixedInclude;
using namespace mixedInclude_ns;
//contained instances forward class declaration
class blockDBase;
template<typename Config> class blockFBase;
class threeCsBase;
class blockBRegsBase;

SC_MODULE(blockB), public blockBase, public blockBBase
{
private:

public:
    // channels
    // An interface for C
    rdy_vld_channel< seeSt > cStuffIf;
    // An interface for C
    rdy_vld_channel< seeSt > cStuff1;
    // An interface for C
    rdy_vld_channel< seeSt > cStuff2;
    // An interface for D
    rdy_vld_channel< dSt > dee0;
    // An interface for D
    rdy_vld_channel< dSt > dee1;
    // An interface for D
    rdy_vld_channel< dSt > loopDF;
    // An interface for D
    rdy_vld_channel< dSt > loopFF;
    // An interface for D
    rdy_vld_channel< dSt > loopFD;
    // A Read Write register
    status_channel< dRegSt > rwD;
    // A Read Only register with a structure that has a definition from an included context
    status_channel< bSizeRegSt > roBsize;
    // Memory register - firmware accessible memory-mapped storage
    memory_channel< bSizeSt, seeSt > blockBTableExt;
    // External 37-bit memory register - firmware accessible with 8-byte stride
    memory_channel< bSizeSt, test37BitRegSt > blockBTable37Bit;

    //instances contained in block
    std::shared_ptr<blockDBase> uBlockD;
    std::shared_ptr<blockFBase<blockFVariant0Config>> uBlockF0;
    std::shared_ptr<blockFBase<blockFVariant1Config>> uBlockF1;
    std::shared_ptr<threeCsBase> uThreeCs;
    std::shared_ptr<blockBRegsBase> uBlockBRegs;

    memories mems;
    //memories
    hwMemory< seeSt > blockBTable0;
    hwMemory< bigSt > blockBTable1;
    hwMemory< seeSt > blockBTable2;
    hwMemory< seeSt > blockBTable3;
    hwMemory< seeSt > blockBTableSP0;
    hwMemory< nestedSt > blockBTableSP;
    memory_channel<bSizeSt, bigSt> blockBTable1_port1;
    memory_channel<bSizeSt, nestedSt> blockBTableSP_bob;
    memory_channel<bSizeSt, bigSt> blockBTable1_reg;

    blockB(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockB() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        blockBBase::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END
    // block implementation members
    void doneTest(void);
};

#endif //BLOCKB_H
