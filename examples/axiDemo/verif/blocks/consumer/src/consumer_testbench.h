#ifndef CONSUMER_TESTBENCH_H_
#define CONSUMER_TESTBENCH_H_

#include "systemc.h"

#include "consumer_base.h"
#include "consumer_hdl_sc_wrapper.h"
#include "consumer_traffic_generator.h"

class consumer_testbench: public sc_module, public consumerChannels {

public:

    consumer_hdl_sc_wrapper *dut_i;
    consumer_traffic_generator *tgen_i;

    consumer_testbench(sc_module_name modulename) :
        consumerChannels("Chnl", "tb")
    {

        dut_i = new consumer_hdl_sc_wrapper("dut_i", "", BLOCKBASEMODE_NOFACTORY);

        tgen_i = new consumer_traffic_generator("tgen_i");

        bind(dut_i, tgen_i);

    }

};

#endif /* CONSUMER_TESTBENCH_H_ */
