#ifndef RDY_VLD_BFM_H_
#define RDY_VLD_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <optional>
#include "rdy_vld_channel.h"
#include "rdy_vld_src_driver.h"
#include "bfmContractCheck.h"

template<typename VL_DATA_T>
struct rdy_vld_hdl_if: public sc_interface {
    sc_signal<bool> vld;
    sc_signal<VL_DATA_T> data;
    sc_signal<bool> rdy;
};

template<typename DATA_T, typename VL_DATA_T>
class rdy_vld_src_bfm: public sc_module {

public:

    rdy_vld_out<DATA_T> if_p;
    sc_port<rdy_vld_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (rdy_vld_src_bfm);

    rdy_vld_src_bfm(sc_module_name modulename) :
        m_lostBeats(name(), "HDL transferred a beat the BFM did not sample", "beats"),
        m_scStalls(name(), "SystemC stalled a backpressure: false producer", "clock edges") {
        SC_THREAD(bfm_driver_thread);
        SC_METHOD(transfer_monitor);
        sensitive << clk.pos();
        dont_initialize();
    }

    virtual void end_of_elaboration() {
        m_noBackpressure = bfmNoBackpressure(if_p.get_interface(), name());
        if_p->setCycleTransaction();
        m_driver.emplace(if_p, clk, rst_n, hdl_if_p->vld, hdl_if_p->rdy,
                         [this](DATA_T &data) { data.sc_unpack(hdl_if_p->data); });
    }

    virtual void end_of_simulation() {
        checkLostBeats(m_sampledBeats);
        m_lostBeats.report();
        m_scStalls.report();
    }

    void bfm_driver_thread() {
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        m_driver->run([this](DATA_T &data) {
            // A beat sampled in reset is still delivered, but the monitor
            // counts only transfers out of reset.
            if (rst_n) {
                m_sampledBeats++;
                m_lastSampleTime = sc_time_stamp();
            }
            if_p->writeClocked(data);
        }, nullptr);
    }

    // The driver wakes on the same edge in either order, so this checks the
    // beats sampled up to the previous edge before counting this edge.
    void transfer_monitor() {
        m_driver->sampleEdge();
        checkLostBeats(m_sampledBeats - (m_lastSampleTime == sc_time_stamp() ? 1 : 0));
        m_lastEdge = sc_time_stamp();
        if (!rst_n || !hdl_if_p->vld) {
            return;
        }
        if (hdl_if_p->rdy) {
            m_hdlBeats++;
        } else if (m_noBackpressure) {
            m_scStalls.fail(sc_time_stamp());
        }
    }

private:

    void checkLostBeats(uint64_t sampledBeats) {
        while (m_hdlBeats > sampledBeats + m_lostBeats.count_) {
            m_lostBeats.fail(m_lastEdge);
        }
    }

    std::optional<rdyVldSrcDriver<DATA_T>> m_driver;
    bool m_noBackpressure = false;
    uint64_t m_hdlBeats = 0;
    uint64_t m_sampledBeats = 0;
    sc_time m_lastSampleTime;
    sc_time m_lastEdge;
    bfmContractCheck m_lostBeats;
    bfmContractCheck m_scStalls;

};

template<typename DATA_T, typename VL_DATA_T>
class rdy_vld_dst_bfm: public sc_module {

public:

    rdy_vld_in<DATA_T> if_p;
    sc_port<rdy_vld_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (rdy_vld_dst_bfm);

    rdy_vld_dst_bfm(sc_module_name modulename) :
        m_stalls(name(), "HDL stalled a backpressure: false interface", "clock edges") {
        SC_THREAD(bfm_driver_thread);
    }

    virtual void end_of_elaboration() {
        m_noBackpressure = bfmNoBackpressure(if_p.get_interface(), name());
        if_p->setCycleTransaction();
    }

    virtual void end_of_simulation() {
        m_stalls.report();
    }

    void bfm_driver_thread() {
        DATA_T data;
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            hdl_if_p->vld = 0;
            hdl_if_p->data = VL_DATA_T(0);
            if_p->peek(data);
            hdl_if_p->vld = 1;
            hdl_if_p->data = data.sc_pack();
            do {
                wait(clk.posedge_event());
                if (m_noBackpressure && rst_n && !hdl_if_p->rdy) {
                    m_stalls.fail(sc_time_stamp());
                }
            } while (!hdl_if_p->rdy);
            // The model's write returns at the edge where the RTL takes the beat.
            if_p->readClocked(data);
        }
    }

private:

    bool m_noBackpressure = false;
    bfmContractCheck m_stalls;

};

#endif /* RDY_VLD_BFM_H_ */
