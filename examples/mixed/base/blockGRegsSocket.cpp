// GENERATED_CODE_PARAM --block=blockGRegs
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "blockGRegsSocket.h"

template<> blockGRegsSocket<mixedDefaultConfig>::registerBlock blockGRegsSocket<mixedDefaultConfig>::registerBlock_(""); //register the block with the factory

template<typename Config>
blockGRegsSocket<Config>::blockGRegsSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockGRegs", name(), bbMode)
        ,blockGRegsBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
