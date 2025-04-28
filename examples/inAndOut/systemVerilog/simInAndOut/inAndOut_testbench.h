#ifndef INANDOUT_TESTBENCH_H_
#define INANDOUT_TESTBENCH_H_

#include "systemc.h"

#include "inAndOut_hdl_sc_wrapper.h"
#include "inAndOut_traffic_generator.h"

class inAndOut_testbench: public sc_module {

public:

    inAndOut_hdl_sc_wrapper *dut_i;
    inAndOut_traffic_generator *tgen_i;

    rdy_vld_channel<aSt> aOut;
    rdy_vld_channel<aSt> aIn;
    req_ack_channel<bSt, bBSt> bOut;
    req_ack_channel<bSt, bBSt> bIn;
    pop_ack_channel<dSt> dOut;
    pop_ack_channel<dSt> dIn;

    inAndOut_testbench(sc_module_name modulename) :
        aOut("aOut", "testBlock"),
        aIn("aIn", "testBlock"),
        bOut("bOut", "testBlock"),
        bIn("bIn", "testBlock"),
        dOut("dOut", "testBlock"),
        dIn("dIn", "testBlock")
    {

        dut_i = new inAndOut_hdl_sc_wrapper("dut_i", "", BLOCKBASEMODE_NOFACTORY);

        dut_i->aOut(aOut);
        dut_i->aIn(aIn);
        dut_i->bOut(bOut);
        dut_i->bIn(bIn);
        dut_i->dOut(dOut);
        dut_i->dIn(dIn);

        tgen_i = new inAndOut_traffic_generator("tgen_i");

        tgen_i->aOut(aOut);
        tgen_i->aIn(aIn);
        tgen_i->bOut(bOut);
        tgen_i->bIn(bIn);
        tgen_i->dOut(dOut);
        tgen_i->dIn(dIn);

    }

};

#endif /* INANDOUT_TESTBENCH_H_ */
