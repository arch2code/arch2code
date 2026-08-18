// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "producerSocket.h"

SC_HAS_PROCESS(producerSocket);

producerSocket::registerBlock producerSocket::registerBlock_; //register the block with the factory

void producerSocket::src_trans_dest_trans_rv_trackerSocket(void) {
    port_socket(src_trans_dest_trans_rv_tracker, "producer.src_trans_dest_trans_rv_tracker");
}

void producerSocket::src_clock_dest_trans_rv_trackerSocket(void) {
    port_socket(src_clock_dest_trans_rv_tracker, "producer.src_clock_dest_trans_rv_tracker");
}

void producerSocket::src_trans_dest_clock_rv_trackerSocket(void) {
    port_socket(src_trans_dest_clock_rv_tracker, "producer.src_trans_dest_clock_rv_tracker");
}

void producerSocket::src_trans_dest_trans_rv_sizeSocket(void) {
    port_socket(src_trans_dest_trans_rv_size, "producer.src_trans_dest_trans_rv_size");
}

void producerSocket::src_clock_dest_trans_rv_sizeSocket(void) {
    port_socket(src_clock_dest_trans_rv_size, "producer.src_clock_dest_trans_rv_size");
}

void producerSocket::src_trans_dest_clock_rv_sizeSocket(void) {
    port_socket(src_trans_dest_clock_rv_size, "producer.src_trans_dest_clock_rv_size");
}

producerSocket::producerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("producer", name(), bbMode)
        ,producerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(src_trans_dest_trans_rv_trackerSocket);
    SC_THREAD(src_clock_dest_trans_rv_trackerSocket);
    SC_THREAD(src_trans_dest_clock_rv_trackerSocket);
    SC_THREAD(src_trans_dest_trans_rv_sizeSocket);
    SC_THREAD(src_clock_dest_trans_rv_sizeSocket);
    SC_THREAD(src_trans_dest_clock_rv_sizeSocket);

// GENERATED_CODE_END
}
