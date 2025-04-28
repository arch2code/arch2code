#ifndef SOMERAPPER_TESTBENCH_H_
#define SOMERAPPER_TESTBENCH_H_

#include "systemc.h"

#include "someRapper_base.h"
#include "someRapper_hdl_sc_wrapper.h"
#include "someRapper_traffic_generator.h"

class someRapper_testbench: public sc_module, public someRapperChannels {

public:

    someRapper_hdl_sc_wrapper *dut_i;
    someRapper_traffic_generator *tgen_i;

    someRapper_testbench(sc_module_name modulename) :
        someRapperChannels("Chnl", "tb")
    {

        dut_i = new someRapper_hdl_sc_wrapper("dut_i", "", BLOCKBASEMODE_NOFACTORY);

        tgen_i = new someRapper_traffic_generator("tgen_i");

        bind(dut_i, tgen_i);

    }

};

#endif /* SOMERAPPER_TESTBENCH_H_ */
