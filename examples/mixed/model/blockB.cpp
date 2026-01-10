//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "endOfTest.h"
#include "testController.h"
// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockB.h"
#include "blockDBase.h"
#include "blockFBase.h"
#include "threeCsBase.h"
#include "blockBRegsBase.h"
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
        ,rwD("blockB_rwD", "blockB", dRegSt::_packedSt(0x0))
        ,roBsize("blockB_roBsize", "blockB", bSizeRegSt::_packedSt(0x0))
        ,blockBTableExt("blockB_blockBTableExt", "blockB")
        ,blockBTable37Bit("blockB_blockBTable37Bit", "blockB")
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
        ,blockBTable1_port1("blockBTable1_port1", "blockB")
        ,blockBTableSP_bob("blockBTableSP_bob", "blockB")
        ,blockBTable1_reg("blockBTable1_reg", "blockB")
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
    uBlockD->blockBTableExt(blockBTableExt);
    uBlockBRegs->blockBTableExt(blockBTableExt);
    uBlockD->blockBTable37Bit(blockBTable37Bit);
    uBlockBRegs->blockBTable37Bit(blockBTable37Bit);
    // memory connections
    uBlockD->blockBTable1(blockBTable1_port1);
    blockBTable1.bindPort(blockBTable1_port1);
    uBlockD->blockBTableSP(blockBTableSP_bob);
    blockBTableSP.bindPort(blockBTableSP_bob);
    uBlockBRegs->blockBTable1(blockBTable1_reg);
    blockBTable1.bindPort(blockBTable1_reg);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(doneTest);
}

void blockB::doneTest(void)
{
    endOfTest eot;
    eot.registerVoter();
    startDone->waitNotify();
    startDone->ack();
    // Do not end the simulation until all registered tests have completed.
    // This prevents premature sc_stop() (see mixedExternal::eotThread) before
    // late tests like test_mem_hier_cpu_read run.
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}
