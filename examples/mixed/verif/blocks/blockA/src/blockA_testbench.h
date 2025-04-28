#ifndef BLOCKA_TESTBENCH_H_
#define BLOCKA_TESTBENCH_H_

#include "systemc.h"

#include "blockA_base.h"
#include "blockA_hdl_sc_wrapper.h"
#include "blockA_traffic_generator.h"

class blockA_testbench: public sc_module, public blockAChannels {

public:

    blockA_hdl_sc_wrapper *dut_i;
    blockA_traffic_generator *tgen_i;

    blockA_testbench(sc_module_name modulename) :
        blockAChannels("Chnl", "tb")
    {

        dut_i = new blockA_hdl_sc_wrapper("dut_i", "", BLOCKBASEMODE_NOFACTORY);

        tgen_i = new blockA_traffic_generator("tgen_i");

        bind(dut_i, tgen_i);

    }

};

#endif /* BLOCKA_TESTBENCH_H_ */
