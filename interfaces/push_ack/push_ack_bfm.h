#ifndef PUSH_ACK_BFM_H_
#define PUSH_ACK_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "bfmClockEdge.h"
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
    bfmClockEdge m_edge{"clk_edge"};

    SC_HAS_PROCESS (push_ack_src_bfm);

    push_ack_src_bfm(sc_module_name modulename) {
        m_edge.clk(clk);
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        // rst_n is asserted a delta after construction, so sample it at clock
        // edges rather than at time zero.
        do { wait(clk.posedge_event()); } while (!rst_n);
        DATA_T data;
        while (true) {
            hdl_if_p->ack = false;
            // A request the RTL raised at a rising edge has settled by the
            // falling edge, so the model gets it there and its ack is on the
            // wire for the next rising edge. A rising edge still catches a
            // request raised after the falling edge. No request is taken
            // while reset is asserted.
            do {
                wait(clk.posedge_event() | clk.negedge_event());
            } while (!hdl_if_p->push || !rst_n);
            data.sc_unpack(hdl_if_p->data);
            if_p->push(data);
            m_edge.settle();
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
    bfmClockEdge m_edge{"clk_edge"};

    SC_HAS_PROCESS (push_ack_dst_bfm);

    push_ack_dst_bfm(sc_module_name modulename) {
        m_edge.clk(clk);
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        DATA_T data;
        while (true) {
            hdl_if_p->push = false;
            hdl_if_p->data = (VL_DATA_T) (0);
            if_p->pushReceive(data);
            m_edge.settle();
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
