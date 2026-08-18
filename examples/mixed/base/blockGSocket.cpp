// GENERATED_CODE_PARAM --block=blockG
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "blockGSocket.h"

template<> blockGSocket<blockGGvariant0Config>::registerBlock blockGSocket<blockGGvariant0Config>::registerBlock_("gvariant0"); //register the block with the factory

template<typename Config>
blockGSocket<Config>::blockGSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockG", name(), bbMode)
        ,blockGBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
