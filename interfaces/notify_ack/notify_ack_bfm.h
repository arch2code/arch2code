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
        bfmClocks::add(if_p, clk, &m_clock);
        SC_THREAD(bfm_driver_thread);
        SC_METHOD(request_monitor);
        sensitive << clk.pos();
        dont_initialize();
        SC_METHOD(clock_fall);
        sensitive << clk.neg();
        dont_initialize();
    }

    virtual void end_of_simulation() {
        m_held.check_.report();
    }

    // The BFM takes each request in its first clock on the pins, so a
    // model that answers in zero time completes it on the next edge, as a
    // destination whose ack follows notify combinationally does.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            hdl_if_p->ack = false;
            if (!m_clock.waitSamplePoint(clk) || !hdl_if_p->notify) {
                wait(clk.posedge_event());
                continue;
            }
            m_held.take(true);
            m_held.inCall_ = true;
            if_p->notify();
            m_held.inCall_ = false;
            m_clock.waitDrivePoint(clk);
            hdl_if_p->ack = true;
            wait(clk.posedge_event());
            if (rst_n) {
                m_held.check(hdl_if_p->notify, true);
            }
        }
    }

    void request_monitor() {
        m_clock.rose();
        if (rst_n) {
            m_held.monitor(hdl_if_p->notify, true);
        }
    }

    void clock_fall() {
        m_clock.fell();
    }

private:

    bfmSameClockAnswer m_clock;
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

    notify_ack_dst_bfm(sc_module_name modulename) :
        m_lowered(name()),
        m_complete([this] { if_p->ack(); }) {
        bfmClocks::add(if_p, clk, &m_clock);
        SC_THREAD(bfm_driver_thread);
        SC_METHOD(edge_monitor);
        sensitive << clk.pos();
        dont_initialize();
        SC_METHOD(clock_fall);
        sensitive << clk.neg();
        dont_initialize();
    }

    virtual void end_of_simulation() {
        m_lowered.report();
    }

    // The model's notify() blocks until ack(), which the BFM calls at the
    // sample point of the clock whose closing edge takes the notification
    // (bfmSameClockAnswer::waitTaken()), so the BFM holds no notification of
    // its own.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        m_clock.rose();
        auto ready = [this] { return hdl_if_p->ack.read(); };
        while (true) {
            hdl_if_p->notify = false;
            if_p->waitNotify();
            m_clock.waitDrivePoint(clk);
            hdl_if_p->notify = true;
            const bool certain = m_clock.waitTaken(clk, ready, [] {});
            m_complete.start();
            if (certain && !m_clock.waitTakenEdge(clk, rst_n, ready, m_lowered)) {
                do {
                    wait(clk.posedge_event());
                    m_clock.rose();
                } while (!ready());
            }
            hdl_if_p->notify = false;
            m_complete.waitDone();
        }
    }

    void edge_monitor() {
        m_clock.rose();
    }

    void clock_fall() {
        m_clock.fell();
    }

private:

    bfmSameClockAnswer m_clock;
    bfmReadyLowered m_lowered;
    bfmCompleter m_complete;

};

#endif /* NOTIFY_ACK_BFM_H_ */
