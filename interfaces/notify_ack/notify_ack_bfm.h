#ifndef NOTIFY_ACK_BFM_H_
#define NOTIFY_ACK_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "notify_ack_channel.h"
#include "bfmContractCheck.h"

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

    notify_ack_src_bfm(sc_module_name modulename) : m_held(name()) {
        SC_THREAD(bfm_driver_thread);
        SC_METHOD(request_monitor);
        sensitive << clk.pos();
        dont_initialize();
    }

    virtual void end_of_simulation() {
        m_held.check_.report();
    }

    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            hdl_if_p->ack = false;
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->notify);
            m_held.take(true);
            m_held.inCall_ = true;
            if_p->notify();
            m_held.inCall_ = false;
            hdl_if_p->ack = true;
            wait(clk.posedge_event());
            if (rst_n) {
                m_held.check(hdl_if_p->notify, true);
            }
        }
    }

    void request_monitor() {
        if (rst_n) {
            m_held.monitor(hdl_if_p->notify, true);
        }
    }

private:

    bfmHeldRequest<bool> m_held;

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

    // The model's notify() blocks until ack(), which the BFM calls on the edge
    // the HDL acks, so the BFM holds no notification of its own.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
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
