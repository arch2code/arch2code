#ifndef CONSUMER_TRAFFIC_GENERATOR_H_
#define CONSUMER_TRAFFIC_GENERATOR_H_

#include "systemc.h"
#include "logging.h"

class consumer_traffic_generator: public sc_module, public consumerInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (consumer_traffic_generator);

    consumer_traffic_generator(sc_module_name modulename) :
        consumerInverted("consumer_traffic_generator"),
        log_("TG")
    {
        SC_THREAD(main_thread);
    }

    void main_thread() {
    }

};

#endif /* CONSUMER_TRAFFIC_GENERATOR_H_ */
