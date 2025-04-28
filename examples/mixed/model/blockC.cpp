//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE


// GENERATED_CODE_PARAM --block=blockC
// GENERATED_CODE_BEGIN --template=constructor --section=init 
#include "blockC.h"
SC_HAS_PROCESS(blockC);

blockC::registerBlock blockC::registerBlock_; //register the block with the factory

blockC::blockC(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockC", name(), bbMode)
        ,blockCBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
}
