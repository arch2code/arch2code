#ifndef BLOCKF_VARIANT0_TRAFFIC_GENERATOR_H_
#define BLOCKF_VARIANT0_TRAFFIC_GENERATOR_H_

#include "systemc.h"
#include "logging.h"

class blockF_variant0_traffic_generator : public sc_module, public blockFInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (blockF_variant0_traffic_generator);

    blockF_variant0_traffic_generator(sc_module_name modulename) :
        blockFInverted("blockF_variant0_traffic_generator"),
        log_("TG")
    {
        SC_THREAD(main_thread);
    }

    void main_thread() {

        wait(1, SC_US);

    }

};

#endif /* BLOCKF_VARIANT0_TRAFFIC_GENERATOR_H_ */
