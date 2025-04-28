#ifndef NOTIFY_ACK_BFM_H_
#define NOTIFY_ACK_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "notify_ack_channel.h"

// note : use dummy template argument <class T = bool>, for consistency with other interfaces

template <class T = bool>
struct notify_ack_hdl_if: public sc_interface {
    sc_signal<bool> notify;
    sc_signal<bool> ack;
};

template <class T = bool>
class notify_ack_src_bfm: public sc_module {

public:

    notify_ack_out<T> if_p;
    sc_port<notify_ack_hdl_if<T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (notify_ack_src_bfm);

    notify_ack_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        while (true) {
            hdl_if_p->ack = false;
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->notify);
            if_p->notify();
            hdl_if_p->ack = true;
            wait(clk.posedge_event());
        }
    }

};

template <class T = bool>
class notify_ack_dst_bfm: public sc_module {

public:

    notify_ack_in<T> if_p;
    sc_port<notify_ack_hdl_if<T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (notify_ack_dst_bfm);

    notify_ack_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        while (true) {
            hdl_if_p->notify = false;
            if_p->waitNotify();
            do {
                hdl_if_p->notify = true;
                wait(clk.posedge_event());
            } while (!hdl_if_p->ack);
            hdl_if_p->notify = false;
            if_p->ack();
        }
    }

};

#endif /* NOTIFY_ACK_BFM_H_ */
