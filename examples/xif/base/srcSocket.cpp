// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "srcSocket.h"

template<> srcSocket<srcSrcV0Config>::registerBlock srcSocket<srcSrcV0Config>::registerBlock_("srcV0"); //register the block with the factory

template<typename Config>
void srcSocket<Config>::outSocket(void) {
    port_socket(this->out, "src.out");
}

template<typename Config>
srcSocket<Config>::srcSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("src", name(), bbMode)
        ,srcBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(outSocket);

// GENERATED_CODE_END
}
