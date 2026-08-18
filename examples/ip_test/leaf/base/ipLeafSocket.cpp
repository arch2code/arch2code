// GENERATED_CODE_PARAM --block=ipLeaf
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "ipLeafSocket.h"

template<> ipLeafSocket<ipLeafVariantLeaf0Config>::registerBlock ipLeafSocket<ipLeafVariantLeaf0Config>::registerBlock_("variantLeaf0"); //register the block with the factory

template<typename Config>
ipLeafSocket<Config>::ipLeafSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipLeaf", name(), bbMode)
        ,ipLeafBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
