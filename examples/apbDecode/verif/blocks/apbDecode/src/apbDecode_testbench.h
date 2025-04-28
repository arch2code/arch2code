#ifndef APBDECODE_TESTBENCH_H_
#define APBDECODE_TESTBENCH_H_

#include "systemc.h"

#include "apbDecode_base.h"
#include "apbDecode_hdl_sc_wrapper.h"
#include "apbDecode_traffic_generator.h"

class apbDecode_testbench: public sc_module, public apbDecodeChannels {

public:

    apbDecode_hdl_sc_wrapper *dut_i;
    apbDecode_traffic_generator *tgen_i;

    apbDecode_testbench(sc_module_name modulename) :
        apbDecodeChannels("Chnl", "tb")
    {

        dut_i = new apbDecode_hdl_sc_wrapper("dut_i", "", BLOCKBASEMODE_NOFACTORY);

        tgen_i = new apbDecode_traffic_generator("tgen_i");

        bind(dut_i, tgen_i);

    }

};

#endif /* APBDECODE_TESTBENCH_H_ */
