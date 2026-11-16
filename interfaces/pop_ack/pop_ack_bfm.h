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

    pop_ack_dst_bfm(sc_module_name modulename) {
        SC_CTHREAD(bfm_driver_thread, clk.pos());
    }

    // The model's pop() blocks until ack(), which the BFM calls on the edge
    // the HDL acks, so the BFM holds no request of its own.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
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
