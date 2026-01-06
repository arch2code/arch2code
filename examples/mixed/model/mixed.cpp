//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE


// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "mixed.h"
#include "blockABase.h"
#include "apbDecodeBase.h"
#include "blockCBase.h"
#include "blockBBase.h"
SC_HAS_PROCESS(mixed);

mixed::registerBlock mixed::registerBlock_; //register the block with the factory

mixed::mixed(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("mixed", name(), bbMode)
        ,mixedBase(name(), variant)
        ,aStuffIf("blockB_aStuffIf", "blockA")
        ,cStuffIf("blockC_cStuffIf", "blockA")
        ,startDone("blockB_startDone", "blockA")
        ,dupIf("blockB_dupIf", "blockA")
        ,apb_uBlockA("blockA_apb_uBlockA", "apbDecode")
        ,apb_uBlockB("blockB_apb_uBlockB", "apbDecode")
        ,uBlockA(std::dynamic_pointer_cast<blockABase>( instanceFactory::createInstance(name(), "uBlockA", "blockA", "")))
        ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>( instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", "")))
        ,uBlockC(std::dynamic_pointer_cast<blockCBase>( instanceFactory::createInstance(name(), "uBlockC", "blockC", "")))
        ,uBlockB(std::dynamic_pointer_cast<blockBBase>( instanceFactory::createInstance(name(), "uBlockB", "blockB", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uAPBDecode->cpu_main(cpu_main);
    // instance to instance connections via channel
    uBlockA->aStuffIf(aStuffIf);
    uBlockB->btod(aStuffIf);
    uBlockA->cStuffIf(cStuffIf);
    uBlockC->see(cStuffIf);
    uBlockA->startDone(startDone);
    uBlockB->startDone(startDone);
    uBlockA->dupIf(dupIf);
    uBlockB->dupIf(dupIf);
    uAPBDecode->apb_uBlockA(apb_uBlockA);
    uBlockA->apbReg(apb_uBlockA);
    uAPBDecode->apb_uBlockB(apb_uBlockB);
    uBlockB->apbReg(apb_uBlockB);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END

    test_mixed_structs::test(); // Run the test for structures
    log_.logPrint(std::format("Instance {} test completed.", this->name()), LOG_IMPORTANT );

}
