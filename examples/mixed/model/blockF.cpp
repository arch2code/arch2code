//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE


// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=constructor --section=init 
#include "blockF.h"
SC_HAS_PROCESS(blockF);

blockF::registerBlock blockF::registerBlock_; //register the block with the factory

blockF::blockF(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockF", name(), bbMode)
        ,blockFBase(name(), variant)
        ,test(name(), "test", mems, bob)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
}
