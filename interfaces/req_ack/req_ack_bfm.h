#ifndef REQ_ACK_BFM_H_
#define REQ_ACK_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "req_ack_channel.h"
#include "bfmContractCheck.h"

template<typename VL_DATA_T, typename VL_RDATA_T>
struct req_ack_hdl_if: public sc_interface {
    sc_signal<bool> req;
    sc_signal<VL_DATA_T> data;
    sc_signal<bool> ack;
    sc_signal<VL_RDATA_T> rdata;
};

template<typename DATA_T, typename RDATA_T, typename VL_DATA_T, typename VL_RDATA_T>
class req_ack_src_bfm: public sc_module {

public:

    req_ack_out<DATA_T, RDATA_T> if_p;
    sc_port<req_ack_hdl_if<VL_DATA_T, VL_RDATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (req_ack_src_bfm);

    req_ack_src_bfm(sc_module_name modulename) : m_held(name()) {
        bfmClocks::add(if_p, clk);
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
    // destination whose ack follows req combinationally does.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        DATA_T data;
        RDATA_T rdata;
        while (true) {
            hdl_if_p->ack = false;
            hdl_if_p->rdata = VL_RDATA_T(0);
            if (!m_clock.waitSamplePoint(clk) || !hdl_if_p->req) {
                wait(clk.posedge_event());
                continue;
            }
            data.sc_unpack(hdl_if_p->data);
            m_held.take(hdl_if_p->data.read());
            m_held.inCall_ = true;
            if_p->req(data, rdata);
            m_held.inCall_ = false;
            m_clock.waitDrivePoint(clk);
            hdl_if_p->ack = true;
            hdl_if_p->rdata = rdata.sc_pack();
            wait(clk.posedge_event());
            if (rst_n) {
                m_held.check(hdl_if_p->req, hdl_if_p->data.read());
            }
        }
    }

    void request_monitor() {
        m_clock.rose();
        if (rst_n) {
            m_held.monitor(hdl_if_p->req, hdl_if_p->data.read());
        }
    }

    void clock_fall() {
        m_clock.fell();
    }

private:

    bfmSameClockAnswer m_clock;
    bfmHeldRequest<VL_DATA_T> m_held;

};

template<typename DATA_T, typename RDATA_T, typename VL_DATA_T, typename VL_RDATA_T>
class req_ack_dst_bfm: public sc_module {

public:

    req_ack_in<DATA_T, RDATA_T> if_p;
    sc_port<req_ack_hdl_if<VL_DATA_T, VL_RDATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (req_ack_dst_bfm);

    req_ack_dst_bfm(sc_module_name modulename) :
        m_lowered(name(), BFM_READY_LOWERED, "clock edges"),
        m_complete([this] { if_p->ack(m_rdata); }) {
        bfmClocks::add(if_p, clk);
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

    // The model's req() blocks until ack(), which the BFM calls with rdata at
    // the sample point of the clock whose closing edge takes the request
    // (bfmSameClockAnswer::waitTaken()), so the BFM holds no request of its
    // own.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        m_clock.rose();
        auto ready = [this] { return hdl_if_p->ack.read(); };
        while (true) {
            DATA_T data;
            if_p->reqReceive(data);
            m_clock.waitDrivePoint(clk);
            hdl_if_p->req = true;
            hdl_if_p->data = data.sc_pack();
            const bool certain = m_clock.waitTaken(clk, ready, [] {});
            m_rdata.sc_unpack(hdl_if_p->rdata);
            m_complete.start();
            if (certain && !m_clock.waitTakenEdge(clk, rst_n, ready, m_lowered)) {
                do {
                    wait(clk.posedge_event());
                    m_clock.rose();
                } while (!ready());
            }
            hdl_if_p->req = false;
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
    bfmContractCheck m_lowered;
    bfmCompleter m_complete;

};

#endif /* REQ_ACK_BFM_H_ */
