#ifndef POP_ACK_BFM_H_
#define POP_ACK_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "pop_ack_channel.h"

template<typename VL_RDATA_T>
struct pop_ack_hdl_if: public sc_interface {
    sc_signal<bool> pop;
    sc_signal<bool> ack;
    sc_signal<VL_RDATA_T> rdata;
};

template<typename RDATA_T, typename VL_RDATA_T>
class pop_ack_src_bfm: public sc_module {

public:

    pop_ack_out<RDATA_T> if_p;
    sc_port<pop_ack_hdl_if<VL_RDATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (pop_ack_src_bfm);

    pop_ack_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        RDATA_T rdata;
        while (true) {
            hdl_if_p->ack = false;
            hdl_if_p->rdata = VL_RDATA_T(0);
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->pop);
            if_p->pop(rdata);
            hdl_if_p->ack = true;
            hdl_if_p->rdata = rdata.sc_pack();
            wait(clk.posedge_event());
        }
    }

};

template<typename RDATA_T, typename VL_RDATA_T>
class pop_ack_dst_bfm: public sc_module {

public:

    pop_ack_in<RDATA_T> if_p;
    sc_port<pop_ack_hdl_if<VL_RDATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (pop_ack_dst_bfm);

    pop_ack_dst_bfm(sc_module_name modulename) {
        SC_CTHREAD(bfm_driver_thread, clk.pos());
    }

    void bfm_driver_thread() {
        while (true) {
            RDATA_T rdata;
            if_p->popReceive();
            hdl_if_p->pop = true;
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->ack);
            rdata.sc_unpack(hdl_if_p->rdata);
            if_p->ack(rdata);
            hdl_if_p->pop = false;
            wait(clk.posedge_event());
        }
    }

};

#endif /* POP_ACK_BFM_H_ */
