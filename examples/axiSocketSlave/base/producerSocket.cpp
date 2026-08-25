// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "producerSocket.h"

SC_HAS_PROCESS(producerSocket);

producerSocket::registerBlock producerSocket::registerBlock_; //register the block with the factory

producerSocket::producerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("producer", name(), bbMode)
        ,producerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
