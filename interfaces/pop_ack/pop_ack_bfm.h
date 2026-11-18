#ifndef POP_ACK_BFM_H_
#define POP_ACK_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "pop_ack_channel.h"
#include "bfmContractCheck.h"

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

    pop_ack_src_bfm(sc_module_name modulename) : m_held(name()) {
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
    // destination whose ack follows pop combinationally does.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        RDATA_T rdata;
        while (true) {
            hdl_if_p->ack = false;
            hdl_if_p->rdata = VL_RDATA_T(0);
            if (!m_clock.waitSamplePoint(clk) || !hdl_if_p->pop) {
                wait(clk.posedge_event());
                continue;
            }
            m_held.take(true);
            m_held.inCall_ = true;
            if_p->pop(rdata);
            m_held.inCall_ = false;
            m_clock.waitDrivePoint(clk);
            hdl_if_p->ack = true;
            hdl_if_p->rdata = rdata.sc_pack();
            wait(clk.posedge_event());
            if (rst_n) {
                m_held.check(hdl_if_p->pop, true);
            }
        }
    }

    void request_monitor() {
        m_clock.rose();
        if (rst_n) {
            m_held.monitor(hdl_if_p->pop, true);
        }
    }

    void clock_fall() {
        m_clock.fell();
    }

private:

    bfmSameClockAnswer m_clock;
    bfmHeldRequest<bool> m_held;

};

template<typename RDATA_T, typename VL_RDATA_T>
class pop_ack_dst_bfm: public sc_module {

public:

    pop_ack_in<RDATA_T> if_p;
    sc_port<pop_ack_hdl_if<VL_RDATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (pop_ack_dst_bfm);

    pop_ack_dst_bfm(sc_module_name modulename) :
        m_lowered(name()),
        m_complete([this] { if_p->ack(m_rdata); }) {
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

    // The model's pop() blocks until ack(), which the BFM calls with rdata at
    // the sample point of the clock whose closing edge takes the request
    // (bfmSameClockAnswer::waitTaken()), so the BFM holds no request of its
    // own.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        m_clock.rose();
        auto ready = [this] { return hdl_if_p->ack.read(); };
        while (true) {
            if_p->popReceive();
            m_clock.waitDrivePoint(clk);
            hdl_if_p->pop = true;
            const bool certain = m_clock.waitTaken(clk, ready, [] {});
            m_rdata.sc_unpack(hdl_if_p->rdata);
            m_complete.start();
            if (certain && !m_clock.waitTakenEdge(clk, rst_n, ready, m_lowered)) {
                do {
                    wait(clk.posedge_event());
                    m_clock.rose();
                } while (!ready());
            }
            hdl_if_p->pop = false;
            m_complete.waitDone();
            wait(clk.posedge_event());
            m_clock.rose();
        }
    }

    void edge_monitor() {
        m_clock.rose();
    }

    void clock_fall() {
        m_clock.fell();
    }

private:

    RDATA_T m_rdata;
    bfmSameClockAnswer m_clock;
    bfmReadyLowered m_lowered;
    bfmCompleter m_complete;

};

#endif /* POP_ACK_BFM_H_ */
