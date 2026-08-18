// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "srcSocket.h"

template<> srcSocket<srcVariantSrc0Config>::registerBlock srcSocket<srcVariantSrc0Config>::registerBlock_("variantSrc0"); //register the block with the factory

template<typename Config>
void srcSocket<Config>::out0Socket(void) {
    port_socket(this->out0, "src.out0");
}

template<typename Config>
void srcSocket<Config>::out1Socket(void) {
    port_socket(this->out1, "src.out1");
}

template<typename Config>
void srcSocket<Config>::out2Socket(void) {
    port_socket(this->out2, "src.out2");
}

template<typename Config>
void srcSocket<Config>::out3Socket(void) {
    port_socket(this->out3, "src.out3");
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
    SC_THREAD(out0Socket);
    SC_THREAD(out1Socket);
    SC_THREAD(out2Socket);
    SC_THREAD(out3Socket);

// GENERATED_CODE_END
}
