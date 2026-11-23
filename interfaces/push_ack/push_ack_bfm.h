#ifndef PUSH_ACK_BFM_H_
#define PUSH_ACK_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "push_ack_channel.h"
#include "bfmContractCheck.h"

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

    push_ack_src_bfm(sc_module_name modulename) : m_held(name()) {
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
    // destination whose ack follows push combinationally does.
    void bfm_driver_thread() {
        // rst_n is asserted a delta after construction, so sample it at clock
        // edges rather than at time zero.
        do { wait(clk.posedge_event()); } while (!rst_n);
        DATA_T data;
        while (true) {
            hdl_if_p->ack = false;
            if (!m_clock.waitSamplePoint(clk) || !hdl_if_p->push) {
                wait(clk.posedge_event());
                continue;
            }
            data.sc_unpack(hdl_if_p->data);
            m_held.take(hdl_if_p->data.read());
            m_held.inCall_ = true;
            if_p->push(data);
            m_held.inCall_ = false;
            m_clock.waitDrivePoint(clk);
            hdl_if_p->ack = true;
            wait(clk.posedge_event());
            if (rst_n) {
                m_held.check(hdl_if_p->push, hdl_if_p->data.read());
            }
        }
    }

    void request_monitor() {
        m_clock.rose();
        if (rst_n) {
            m_held.monitor(hdl_if_p->push, hdl_if_p->data.read());
        }
    }

    void clock_fall() {
        m_clock.fell();
    }

private:

    bfmSameClockAnswer m_clock;
    bfmHeldRequest<VL_DATA_T> m_held;

};

template<typename DATA_T, typename VL_DATA_T>
class push_ack_dst_bfm: public sc_module {

public:

    push_ack_in<DATA_T> if_p;
    sc_port<push_ack_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (push_ack_dst_bfm);

    push_ack_dst_bfm(sc_module_name modulename) :
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

    // pushReceive() copies the value, but the model's push() blocks until
    // ack(). The BFM calls it at the sample point of the clock whose closing
    // edge takes the push (bfmSameClockAnswer::waitTaken()), so the push
    // stays the model's outstanding write and the BFM holds no value of its
    // own. A push whose ack falls after that point stays on the pins until
    // the HDL takes it.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        m_clock.rose();
        DATA_T data;
        auto ready = [this] { return hdl_if_p->ack.read(); };
        while (true) {
            hdl_if_p->push = false;
            hdl_if_p->data = (VL_DATA_T) (0);
            if_p->pushReceive(data);
            m_clock.waitDrivePoint(clk);
            hdl_if_p->push = true;
            hdl_if_p->data = data.sc_pack();
            const bool certain = m_clock.waitTaken(clk, ready, [] {});
            m_complete.start();
            if (certain && !m_clock.waitTakenEdge(clk, rst_n, ready, m_lowered)) {
                do {
                    wait(clk.posedge_event());
                    m_clock.rose();
                } while (!ready());
            }
            hdl_if_p->push = false;
            hdl_if_p->data = (VL_DATA_T) (0);
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

#endif /* PUSH_ACK_BFM_H_ */
