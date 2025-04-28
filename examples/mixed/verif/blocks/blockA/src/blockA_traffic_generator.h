#ifndef BLOCKA_TRAFFIC_GENERATOR_H_
#define BLOCKA_TRAFFIC_GENERATOR_H_

#include "systemc.h"
#include "logging.h"

class blockA_traffic_generator: public sc_module, public blockAInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (blockA_traffic_generator);

    blockA_traffic_generator(sc_module_name modulename) :
        blockAInverted("blockA_traffic_generator"),
        log_("TG")
    {
        SC_THREAD(main_thread);
    }

    void main_thread() {

        wait(1, SC_US);

    }

};

#endif /* BLOCKA_TRAFFIC_GENERATOR_H_ */
