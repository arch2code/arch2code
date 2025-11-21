#ifndef PUSH_ACK_BFM_H_
#define PUSH_ACK_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "push_ack_channel.h"

template<typename VL_DATA_T>
struct push_ack_hdl_if: public sc_interface {
    sc_signal<bool> push;
    sc_signal<VL_DATA_T> data;
    sc_signal<bool> ack;
};

template<typename DATA_T, typename VL_DATA_T>
class push_ack_src_bfm: public sc_module {

public:

    push_ack_out<DATA_T> if_p;
    sc_port<push_ack_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (push_ack_src_bfm);

    push_ack_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        DATA_T data;
        while (true) {
            hdl_if_p->ack = false;
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->push);
            data.sc_unpack(hdl_if_p->data);
            if_p->push(data);
            hdl_if_p->ack = true;
            wait(clk.posedge_event());
        }
    }

};

template<typename DATA_T, typename VL_DATA_T>
class push_ack_dst_bfm: public sc_module {

public:

    push_ack_in<DATA_T> if_p;
    sc_port<push_ack_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (push_ack_dst_bfm);

    push_ack_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        DATA_T data;
        while (true) {
            hdl_if_p->push = false;
            hdl_if_p->data = (VL_DATA_T) (0);
            if_p->pushReceive(data);
            do {
                hdl_if_p->push = true;
                hdl_if_p->data = data.sc_pack();
                wait(clk.posedge_event());
            } while (!hdl_if_p->ack);
            hdl_if_p->push = false;
            hdl_if_p->data = (VL_DATA_T) (0);
            if_p->ack();
        }
    }

};

#endif /* PUSH_ACK_BFM_H_ */
