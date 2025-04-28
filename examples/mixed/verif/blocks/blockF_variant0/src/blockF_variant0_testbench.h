#ifndef BLOCKF_VARIANT0_TESTBENCH_H_
#define BLOCKF_VARIANT0_TESTBENCH_H_

#include "systemc.h"

#include "vl_wrap.h"

#include "blockF_base.h"
#include "blockF_variant0_traffic_generator.h"

class blockF_variant0_testbench: public sc_module, public blockFChannels {

public:

    blockF_variant0_hdl_sc_wrapper *dut_i;
    blockF_variant0_traffic_generator *tgen_i;

    blockF_variant0_testbench(sc_module_name modulename) :
        blockFChannels("Chnl", "tb")
    {

        dut_i = new blockF_variant0_hdl_sc_wrapper("dut_i", "variant0", BLOCKBASEMODE_NOFACTORY);
        tgen_i = new blockF_variant0_traffic_generator("tgen_i");

        bind(dut_i, tgen_i);

    }

};

#endif /* BLOCKF_VARIANT0_TESTBENCH_H_ */
