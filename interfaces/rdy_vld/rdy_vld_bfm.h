#ifndef RDY_VLD_BFM_H_
#define RDY_VLD_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "rdy_vld_channel.h"
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
        m_scStalls(name(), "SystemC stalled a backpressure: false producer", "clock edges"),
        m_paced(name()) {
        SC_THREAD(bfm_driver_thread);
        SC_METHOD(transfer_monitor);
        sensitive << clk.pos();
        dont_initialize();
    }

    virtual void end_of_elaboration() {
        m_noBackpressure = bfmNoBackpressure(if_p.get_interface(), name());
        if_p->setCycleTransaction();
        m_chnl = dynamic_cast<rdy_vld_channel<DATA_T> *>(if_p.get_interface());
        Q_ASSERT_CTX(m_chnl != nullptr, name(), "BFM is bound to an interface that is not a rdy_vld_channel");
        m_chnl->setHdlWriter();
        m_paced.port_ = m_chnl->name();
    }

    virtual void end_of_simulation() {
        checkLostBeats(m_sampledBeats);
        m_lostBeats.report();
        m_scStalls.report();
    }

    // rdy tells the HDL whether the reader takes a beat on the next edge, so
    // it is driven from the channel after the reader's zero-time work at this
    // edge: one time resolution step after it, before the falling edge where
    // UVM monitors sample. A reader that has taken a beat and not come back
    // for the next leaves rdy low, so the BFM never holds a beat the reader
    // has no room for. A reader leaves read() only with a beat, so rdy that
    // is high on an edge with no transfer stays high without a new sample.
    void bfm_driver_thread() {
        DATA_T data;
        bool sample = true;
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            if (sample) {
                wait(sc_get_time_resolution());
                hdl_if_p->rdy = if_p->get_rdy();
            }
            wait(clk.posedge_event());
            if (!(hdl_if_p->vld && hdl_if_p->rdy)) {
                sample = !hdl_if_p->rdy;
                continue;
            }
            sample = true;
            m_paced.transfer(sc_time_stamp(), m_chnl->readEnteredTime(), m_chnl->readEnteredDelta());
            // A beat sampled in reset is still delivered, but the monitor
            // counts only transfers out of reset.
            if (rst_n) {
                m_sampledBeats++;
                m_lastSampleTime = sc_time_stamp();
            }
            data.sc_unpack(hdl_if_p->data);
            // A delayed write blocks across clock edges, and the HDL must not
            // transfer on them.
            hdl_if_p->rdy = false;
            if_p->writeClocked(data);
        }
    }

    // The driver wakes on the same edge in either order, so this checks the
    // beats sampled up to the previous edge before counting this edge.
    void transfer_monitor() {
        checkLostBeats(m_sampledBeats - (m_lastSampleTime == sc_time_stamp() ? 1 : 0));
        m_lastEdge = sc_time_stamp();
        m_paced.edge(m_lastEdge);
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

    rdy_vld_channel<DATA_T> *m_chnl = nullptr;
    bool m_noBackpressure = false;
    uint64_t m_hdlBeats = 0;
    uint64_t m_sampledBeats = 0;
    sc_time m_lastSampleTime;
    sc_time m_lastEdge;
    bfmContractCheck m_lostBeats;
    bfmContractCheck m_scStalls;
    bfmClockPaced m_paced;

};

template<typename DATA_T, typename VL_DATA_T>
class rdy_vld_dst_bfm: public sc_module {

public:

    rdy_vld_in<DATA_T> if_p;
    sc_port<rdy_vld_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (rdy_vld_dst_bfm);

    ::sc_core::sc_process_handle rdy_control_thread_handle;

    rdy_vld_dst_bfm(sc_module_name modulename) :
        m_stalls(name(), "HDL stalled a backpressure: false interface", "clock edges"),
        m_paced(name()) {
        SC_THREAD(bfm_driver_thread);
        SC_METHOD(edge_monitor);
        sensitive << clk.pos();
        dont_initialize();
        //SC_METHOD(rdy_control_thread);
        rdy_control_thread_handle =
            sc_core::sc_get_curr_simcontext()->create_method_process("rdy_control_thread", false,
                static_cast<sc_core::SC_ENTRY_FUNC>(&SC_CURRENT_USER_MODULE::rdy_control_thread), this, 0);
    }

    virtual void end_of_elaboration() {
        //this->sensitive << rdy_control_thread_handle <<  hdl_if_p->rdy;
        //if_p->enable_user_ready_control(); // delayed until here to ensure the port is bound
        m_noBackpressure = bfmNoBackpressure(if_p.get_interface(), name());
        if_p->setCycleTransaction();
        m_chnl = dynamic_cast<rdy_vld_channel<DATA_T> *>(if_p.get_interface());
        Q_ASSERT_CTX(m_chnl != nullptr, name(), "BFM is bound to an interface that is not a rdy_vld_channel");
        m_paced.port_ = m_chnl->name();
        if_p->setExternalEvent(&m_offer);
    }

    virtual void end_of_simulation() {
        m_stalls.report();
    }

    // A value stays the writer's until the HDL takes it. The BFM shows the
    // offered value on the pins and reads it on the edge that transfers it,
    // so the writer blocks as it would on the RTL's output register and the
    // BFM holds no value of its own. A multicycle channel's burst is read
    // when its first beat goes on the pins.
    void bfm_driver_thread() {
        DATA_T data;
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            hdl_if_p->vld = 0;
            hdl_if_p->data = VL_DATA_T(0);
            const bool multiCycle = m_chnl->isMultiCycle();
            if (multiCycle) {
                if_p->readClocked(data);
            } else {
                while (!m_chnl->offered(data)) {
                    wait(m_offer);
                }
            }
            hdl_if_p->vld = 1;
            hdl_if_p->data = data.sc_pack();
            do {
                wait(clk.posedge_event());
                if (m_noBackpressure && rst_n && !hdl_if_p->rdy) {
                    m_stalls.fail(sc_time_stamp());
                }
            } while (!hdl_if_p->rdy);
            if (!multiCycle) {
                m_paced.transfer(sc_time_stamp(), m_chnl->writeEnteredTime(), m_chnl->writeEnteredDelta());
                if_p->read(data);
            }
        }
    }

    void edge_monitor() {
        m_paced.edge(sc_time_stamp());
    }

    void rdy_control_thread() {
        if_p->set_rdy(hdl_if_p->rdy);
    }

private:

    rdy_vld_channel<DATA_T> *m_chnl = nullptr;
    sc_event m_offer;
    bool m_noBackpressure = false;
    bfmContractCheck m_stalls;
    bfmClockPaced m_paced;

};

#endif /* RDY_VLD_BFM_H_ */
