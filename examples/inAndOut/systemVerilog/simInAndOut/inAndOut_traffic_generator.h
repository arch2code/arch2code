#ifndef INANDOUT_TRAFFIC_GENERATOR_H_
#define INANDOUT_TRAFFIC_GENERATOR_H_

#include "systemc.h"

class inAndOut_traffic_generator: public sc_module {

public:

    rdy_vld_in<aSt> aOut;
    rdy_vld_out<aSt> aIn;
    req_ack_in<bSt, bBSt> bOut;
    req_ack_out<bSt, bBSt> bIn;
    pop_ack_in<dSt> dOut;
    pop_ack_out<dSt> dIn;

    inAndOut_traffic_generator(sc_module_name modulename) {

    }

};

#endif /* INANDOUT_TRAFFIC_GENERATOR_H_ */
