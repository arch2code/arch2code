//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE


// GENERATED_CODE_PARAM --block=blockD
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockD.h"
SC_HAS_PROCESS(blockD);

blockD::registerBlock blockD::registerBlock_; //register the block with the factory

blockD::blockD(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockD", name(), bbMode)
        ,blockDBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
}
