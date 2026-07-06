//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE


// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockF.h"
template<typename Config>
blockF<Config>::blockF(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockF", name(), bbMode)
        ,blockFBase<Config>(name(), variant)
        ,test(name(), "test", mems, Config::bob)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
}
