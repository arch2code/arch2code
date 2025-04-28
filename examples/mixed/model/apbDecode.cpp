//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "apbDecode.h"
SC_HAS_PROCESS(apbDecode);

apbDecode::registerBlock apbDecode::registerBlock_; //register the block with the factory

void apbDecode::routerDecode(void) //handle apb routing for register
{
    log_.logPrint(fmt::format("SystemC Thread:{} started", __func__));
    decoder.decodeThread();
}

apbDecode::apbDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("apbDecode", name(), bbMode)
        ,apbDecodeBase(name(), variant)
        ,decoder(16, 24, apbReg, {
            &apb_uBlockA,
            &apb_uBlockB})
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    SC_THREAD(routerDecode);
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

