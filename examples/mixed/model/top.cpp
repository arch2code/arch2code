//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE


// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "top.h"
#include "blockA_base.h"
#include "blockC_base.h"
#include "blockB_base.h"
#include "apbDecode_base.h"
#include "cpu_base.h"
SC_HAS_PROCESS(top);

top::registerBlock top::registerBlock_; //register the block with the factory

top::top(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("top", name(), bbMode)
        ,topBase(name(), variant)
        ,aStuffIf("blockB_aStuffIf", "blockA")
        ,cStuffIf("blockC_cStuffIf", "blockA")
        ,startDone("blockB_startDone", "blockA")
        ,apb_uBlockA("blockA_apb_uBlockA", "apbDecode")
        ,apb_uBlockB("blockB_apb_uBlockB", "apbDecode")
        ,apbReg("apbDecode_apbReg", "cpu")
        ,uBlockA(std::dynamic_pointer_cast<blockABase>( instanceFactory::createInstance(name(), "uBlockA", "blockA", "")))
        ,uBlockC(std::dynamic_pointer_cast<blockCBase>( instanceFactory::createInstance(name(), "uBlockC", "blockC", "")))
        ,uBlockB(std::dynamic_pointer_cast<blockBBase>( instanceFactory::createInstance(name(), "uBlockB", "blockB", "")))
        ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>( instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", "")))
        ,uCPU(std::dynamic_pointer_cast<cpuBase>( instanceFactory::createInstance(name(), "uCPU", "cpu", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// instance to instance connections via channel
    uBlockA->aStuffIf(aStuffIf);
    uBlockB->btod(aStuffIf);
    uBlockA->cStuffIf(cStuffIf);
    uBlockC->see(cStuffIf);
    uBlockA->startDone(startDone);
    uBlockB->startDone(startDone);
    uAPBDecode->apb_uBlockA(apb_uBlockA);
    uBlockA->apbReg(apb_uBlockA);
    uAPBDecode->apb_uBlockB(apb_uBlockB);
    uBlockB->apbReg(apb_uBlockB);
    uCPU->apbReg(apbReg);
    uAPBDecode->apbReg(apbReg);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END

    test_mixed_structs::test(); // Run the test for structures
    log_.logPrint(std::format("Instance {} test completed.", this->name()), LOG_IMPORTANT );

}
