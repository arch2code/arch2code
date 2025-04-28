// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE


// GENERATED_CODE_PARAM --block=secondBlock
// GENERATED_CODE_BEGIN --template=constructor --section=init 
#include "secondBlock.h"
#include "secondSubA_base.h"
#include "secondSubB_base.h"
SC_HAS_PROCESS(secondBlock);

secondBlock::registerBlock secondBlock::registerBlock_; //register the block with the factory

secondBlock::secondBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("secondBlock", name(), bbMode)
        ,secondBlockBase(name(), variant)
        ,test("secondSubB_test", "secondSubA")
        ,uSecondSubA(std::dynamic_pointer_cast<secondSubABase>( instanceFactory::createInstance(name(), "uSecondSubA", "secondSubA", "")))
        ,uSecondSubB(std::dynamic_pointer_cast<secondSubBBase>( instanceFactory::createInstance(name(), "uSecondSubB", "secondSubB", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uSecondSubA->primary(primary);
    uSecondSubB->beta(beta);
// instance to instance connections via channel
    uSecondSubA->test(test);
    uSecondSubB->test(test);
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END

}


