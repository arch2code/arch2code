#ifndef BLOCKB_H
#define BLOCKB_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "mixedIncludes.h"

// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "blockB_base.h"
#include "addressMap.h"
#include "hwMemory.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"
#include "mixedIncludeIncludes.h"
//contained instances forward class declaration
class blockDBase;
class blockFBase;
class threeCsBase;
class blockBRegsBase;

SC_MODULE(blockB), public blockBase, public blockBBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockB_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockB>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
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

    //instances contained in block
    std::shared_ptr<blockDBase> uBlockD;
    std::shared_ptr<blockFBase> uBlockF0;
    std::shared_ptr<blockFBase> uBlockF1;
    std::shared_ptr<threeCsBase> uThreeCs;
    std::shared_ptr<blockBRegsBase> uBlockBRegs;

    memories mems;
    //memories
    hwMemory< seeSt > blockBTable0;
    hwMemory< seeSt > blockBTable1;
    hwMemory< seeSt > blockBTable2;
    hwMemory< seeSt > blockBTable3;
    hwMemory< seeSt > blockBTableSP0;
    hwMemory< nestedSt > blockBTableSP;

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
