#ifndef PRODUCER_TRAFFIC_GENERATOR_H_
#define PRODUCER_TRAFFIC_GENERATOR_H_

#include "systemc.h"
#include "logging.h"

class producer_traffic_generator: public sc_module, public producerInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (producer_traffic_generator);

    producer_traffic_generator(sc_module_name modulename) :
        producerInverted("producer_traffic_generator"),
        log_("TG")
    {
        SC_THREAD(main_thread);
    }

    void main_thread() {
    }

};

#endif /* PRODUCER_TRAFFIC_GENERATOR_H_ */
