//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE


// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockB.h"
#include "blockD_base.h"
#include "blockBRegs_base.h"
#include "blockF_base.h"
#include "threeCs_base.h"
SC_HAS_PROCESS(blockB);

blockB::registerBlock blockB::registerBlock_; //register the block with the factory

blockB::blockB(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockB", name(), bbMode)
        ,blockBBase(name(), variant)
        ,cStuffIf_uBlockD_uThreeCs("threeCs_cStuffIf_uBlockD_uThreeCs", "blockD")
        ,dee0("blockF_dee0", "blockD")
        ,dee1("blockF_dee1", "blockD")
        ,rwD("rwD", "blockBRegs")
        ,roBsize("blockBRegs_roBsize", "blockBRegs")
        ,cStuffIf_uBlockF0_uThreeCs("threeCs_cStuffIf_uBlockF0_uThreeCs", "blockF")
        ,cStuffIf_uBlockF1_uThreeCs("threeCs_cStuffIf_uBlockF1_uThreeCs", "blockF")
        ,uBlockD(std::dynamic_pointer_cast<blockDBase>( instanceFactory::createInstance(name(), "uBlockD", "blockD", "")))
        ,uBlockBRegs(std::dynamic_pointer_cast<blockBRegsBase>( instanceFactory::createInstance(name(), "uBlockBRegs", "blockBRegs", "")))
        ,uBlockF0(std::dynamic_pointer_cast<blockFBase>( instanceFactory::createInstance(name(), "uBlockF0", "blockF", "variant0")))
        ,uBlockF1(std::dynamic_pointer_cast<blockFBase>( instanceFactory::createInstance(name(), "uBlockF1", "blockF", "variant1")))
        ,uThreeCs(std::dynamic_pointer_cast<threeCsBase>( instanceFactory::createInstance(name(), "uThreeCs", "threeCs", "")))
        ,blockBTable0(name(), "blockBTable0", mems, BSIZE, HWMEMORYTYPE_LOCAL)
        ,blockBTable1(name(), "blockBTable1", mems, BSIZE)
        ,blockBTable2(name(), "blockBTable2", mems, BSIZE)
        ,blockBTable3(name(), "blockBTable3", mems, BSIZE)
        ,blockBTableSP0(name(), "blockBTableSP0", mems, BSIZE)
        ,blockBTableSP(name(), "blockBTableSP", mems, BSIZE)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uBlockD->btod(btod);
    uBlockBRegs->apbReg(apbReg);
// instance to instance connections via channel
    uBlockD->cStuffIf(cStuffIf_uBlockD_uThreeCs);
    uThreeCs->see0(cStuffIf_uBlockD_uThreeCs);
    uBlockD->dee0(dee0);
    uBlockF0->dStuffIf(dee0);
    uBlockD->dee1(dee1);
    uBlockF1->dStuffIf(dee1);
    uBlockBRegs->rwD(rwD);
    uBlockBRegs->roBsize(roBsize);
    uBlockF0->cStuffIf(cStuffIf_uBlockF0_uThreeCs);
    uThreeCs->see1(cStuffIf_uBlockF0_uThreeCs);
    uBlockF1->cStuffIf(cStuffIf_uBlockF1_uThreeCs);
    uThreeCs->see2(cStuffIf_uBlockF1_uThreeCs);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(doneTest);
}

void blockB::doneTest(void)
{
    startDone->waitNotify();
    startDone->ack();
}