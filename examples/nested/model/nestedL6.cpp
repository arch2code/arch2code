//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL6
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "nestedL6.h"
SC_HAS_PROCESS(nestedL6);

nestedL6::registerBlock nestedL6::registerBlock_; //register the block with the factory

nestedL6::nestedL6(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL6", name(), bbMode)
        ,nestedL6Base(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

