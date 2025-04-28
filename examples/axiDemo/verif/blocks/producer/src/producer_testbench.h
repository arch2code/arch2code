#ifndef PRODUCER_TESTBENCH_H_
#define PRODUCER_TESTBENCH_H_

#include "systemc.h"

#include "producer_base.h"
#include "producer_hdl_sc_wrapper.h"
#include "producer_traffic_generator.h"

class producer_testbench: public sc_module, public producerChannels {

public:

    producer_hdl_sc_wrapper *dut_i;
    producer_traffic_generator *tgen_i;

    producer_testbench(sc_module_name modulename) :
        producerChannels("Chnl", "tb")
    {

        dut_i = new producer_hdl_sc_wrapper("dut_i", "", BLOCKBASEMODE_NOFACTORY);

        tgen_i = new producer_traffic_generator("tgen_i");

        bind(dut_i, tgen_i);

    }

};

#endif /* PRODUCER_TESTBENCH_H_ */
