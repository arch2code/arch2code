// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "consumerSocket.h"

SC_HAS_PROCESS(consumerSocket);

consumerSocket::registerBlock consumerSocket::registerBlock_; //register the block with the factory

void consumerSocket::src_trans_dest_trans_rv_trackerSocket(void) {
    port_socket(src_trans_dest_trans_rv_tracker, "consumer.src_trans_dest_trans_rv_tracker");
}

void consumerSocket::src_clock_dest_trans_rv_trackerSocket(void) {
    port_socket(src_clock_dest_trans_rv_tracker, "consumer.src_clock_dest_trans_rv_tracker");
}

void consumerSocket::src_trans_dest_clock_rv_trackerSocket(void) {
    port_socket(src_trans_dest_clock_rv_tracker, "consumer.src_trans_dest_clock_rv_tracker");
}

void consumerSocket::src_trans_dest_trans_rv_sizeSocket(void) {
    port_socket(src_trans_dest_trans_rv_size, "consumer.src_trans_dest_trans_rv_size");
}

void consumerSocket::src_clock_dest_trans_rv_sizeSocket(void) {
    port_socket(src_clock_dest_trans_rv_size, "consumer.src_clock_dest_trans_rv_size");
}

void consumerSocket::src_trans_dest_clock_rv_sizeSocket(void) {
    port_socket(src_trans_dest_clock_rv_size, "consumer.src_trans_dest_clock_rv_size");
}

consumerSocket::consumerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("consumer", name(), bbMode)
        ,consumerBase(name(), variant)
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
