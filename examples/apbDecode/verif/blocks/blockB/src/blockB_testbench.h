#ifndef BLOCKB_TESTBENCH_H_
#define BLOCKB_TESTBENCH_H_

#include "systemc.h"

#include "blockB_base.h"
#include "blockB_hdl_sc_wrapper.h"
#include "blockB_traffic_generator.h"

class blockB_testbench: public sc_module, public blockBChannels {

public:

    blockB_hdl_sc_wrapper *dut_i;
    blockB_traffic_generator *tgen_i;

    blockB_testbench(sc_module_name modulename) :
        blockBChannels("Chnl", "tb")
    {

        dut_i = new blockB_hdl_sc_wrapper("dut_i", "", BLOCKBASEMODE_NOFACTORY);

        tgen_i = new blockB_traffic_generator("tgen_i");

        bind(dut_i, tgen_i);
    }

};

#endif /* BLOCKB_TESTBENCH_H_ */
