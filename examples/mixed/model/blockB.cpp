//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE


// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockB.h"
#include "blockD_base.h"
#include "blockF_base.h"
#include "threeCs_base.h"
#include "blockBRegs_base.h"
SC_HAS_PROCESS(blockB);

blockB::registerBlock blockB::registerBlock_; //register the block with the factory

blockB::blockB(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockB", name(), bbMode)
        ,blockBBase(name(), variant)
        ,cStuffIf("threeCs_cStuffIf", "blockD")
        ,cStuff1("threeCs_cStuff1", "blockF")
        ,cStuff2("threeCs_cStuff2", "blockF")
        ,dee0("blockF_dee0", "blockD")
        ,dee1("blockF_dee1", "blockD")
        ,loopDF("blockF_loopDF", "blockD")
        ,loopFF("blockF_loopFF", "blockF")
        ,loopFD("blockD_loopFD", "blockF")
        ,rwD("blockB_rwD", "blockB")
        ,roBsize("blockB_roBsize", "blockB")
        ,uBlockD(std::dynamic_pointer_cast<blockDBase>( instanceFactory::createInstance(name(), "uBlockD", "blockD", "")))
        ,uBlockF0(std::dynamic_pointer_cast<blockFBase>( instanceFactory::createInstance(name(), "uBlockF0", "blockF", "variant0")))
        ,uBlockF1(std::dynamic_pointer_cast<blockFBase>( instanceFactory::createInstance(name(), "uBlockF1", "blockF", "variant1")))
        ,uThreeCs(std::dynamic_pointer_cast<threeCsBase>( instanceFactory::createInstance(name(), "uThreeCs", "threeCs", "")))
        ,uBlockBRegs(std::dynamic_pointer_cast<blockBRegsBase>( instanceFactory::createInstance(name(), "uBlockBRegs", "blockBRegs", "")))
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
    uBlockD->cStuffIf(cStuffIf);
    uThreeCs->see0(cStuffIf);
    uBlockF0->cStuffIf(cStuff1);
    uThreeCs->see1(cStuff1);
    uBlockF1->cStuffIf(cStuff2);
    uThreeCs->see2(cStuff2);
    uBlockD->dee0(dee0);
    uBlockF0->dStuffIf(dee0);
    uBlockD->dee1(dee1);
    uBlockF1->dStuffIf(dee1);
    uBlockD->outD(loopDF);
    uBlockF0->dSin(loopDF);
    uBlockF0->dSout(loopFF);
    uBlockF1->dSin(loopFF);
    uBlockF1->dSout(loopFD);
    uBlockD->inD(loopFD);
    uBlockF0->rwD(rwD);
    uBlockBRegs->rwD(rwD);
    uBlockF1->rwD(rwD);
    uBlockD->rwD(rwD);
    uBlockD->roBsize(roBsize);
    uBlockBRegs->roBsize(roBsize);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(doneTest);
}

void blockB::doneTest(void)
{
    startDone->waitNotify();
    startDone->ack();
}