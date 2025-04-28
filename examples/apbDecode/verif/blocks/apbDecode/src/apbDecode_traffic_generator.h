#ifndef APBDECODE_TRAFFIC_GENERATOR_H_
#define APBDECODE_TRAFFIC_GENERATOR_H_

#include "systemc.h"
#include "logging.h"
#include "regAddresses.h"

class apbDecode_traffic_generator: public sc_module, public apbDecodeInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (apbDecode_traffic_generator);

    apbDecode_traffic_generator(sc_module_name modulename) :
        apbDecodeInverted("apbDecode_traffic_generator"),
        log_("TG")
    {
        SC_THREAD(main_thread);
    }

    void main_thread() {
    }

};

#endif /* APBDECODE_TRAFFIC_GENERATOR_H_ */
