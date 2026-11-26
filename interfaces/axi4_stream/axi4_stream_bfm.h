#ifndef AXI4_STREAM_BFM_H_
#define AXI4_STREAM_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "axi4_stream_channel.h"
#include "bfmContractCheck.h"
#include "optionalPayload.h"

// The TUSER sideband is optional, so both of its template arguments sit in the
// argument tail: the payload type TUSER_T and the Verilated bridge type
// VL_TUSER_T. TUSER is a real interface signal, so the HDL boundary keeps a
// tuser port whether or not a payload is bound. When none is, VL_TUSER_T
// defaults to the one-bit placeholder the SystemVerilog interface declares and
// nothing ever drives or samples it.
template<typename VL_TDATA_T, typename VL_TID_T, typename VL_TDEST_T, typename VL_TSTRB_T, typename VL_TKEEP_T,
typename VL_TUSER_T = bool>
struct axi4_stream_hdl_if: public sc_interface {
    sc_signal<bool> tvalid;
    sc_signal<bool> tready;
    sc_signal<VL_TDATA_T> tdata;
    sc_signal<VL_TSTRB_T> tstrb;
    sc_signal<VL_TKEEP_T> tkeep;
    sc_signal<bool> tlast;
    sc_signal<VL_TID_T> tid;
    sc_signal<VL_TDEST_T> tdest;
    sc_signal<VL_TUSER_T> tuser;
};

template<typename TDATA_T, typename TID_T, typename TDEST_T,
typename VL_TDATA_T, typename VL_TID_T, typename VL_TDEST_T, typename VL_TSTRB_T, typename VL_TKEEP_T,
typename VL_TUSER_T = bool, typename TUSER_T = std::monostate>
class axi4_stream_src_bfm: public sc_module {

public:

    axi4_stream_out<TDATA_T, TID_T, TDEST_T, TUSER_T> if_p;
    sc_port<axi4_stream_hdl_if<VL_TDATA_T, VL_TID_T, VL_TDEST_T, VL_TSTRB_T, VL_TKEEP_T, VL_TUSER_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi4_stream_src_bfm);

    axi4_stream_src_bfm(sc_module_name modulename) :
        m_lostBeats(name(), "HDL transferred a beat the BFM did not sample", "beats"),
        m_scStalls(name(), "SystemC stalled a backpressure: false producer", "clock edges"),
        m_paced(name()) {
        bfmClocks::add(if_p, clk, &m_clock);
        SC_THREAD(bfm_driver_thread);
        SC_METHOD(transfer_monitor);
        sensitive << clk.pos();
        dont_initialize();
        SC_METHOD(clock_fall);
        sensitive << clk.neg();
        dont_initialize();
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi4_stream_channel<TDATA_T, TID_T, TDEST_T, TUSER_T> *>(if_p.get_interface());
        m_noBackpressure = bfmNoBackpressure(m_chnl->m_tx_out.get_interface(), name());
        if_p->setCycleTransaction(PORTTYPE_OUT);
        m_tx = dynamic_cast<rdy_vld_channel<axi4StreamInfoSt<TDATA_T, TID_T, TDEST_T, TUSER_T>> *>(m_chnl->m_tx_in.get_interface());
        Q_ASSERT_CTX(m_tx != nullptr, name(), "axi4_stream channel does not carry its beats on a rdy_vld_channel");
        m_paced.port_ = m_chnl->name();
    }

    virtual void end_of_simulation() {
        checkLostBeats(m_sampledBeats);
        m_lostBeats.report();
        m_scStalls.report();
    }

    // tready tells the HDL whether the reader takes a beat on the next edge,
    // so it is driven from the channel after the reader's zero-time work at
    // this edge: one time resolution step after it, before the falling edge
    // where UVM monitors sample. A reader that comes back later in the clock,
    // while it is still high, raises tready then. A reader that has taken a
    // beat and not come back for the next leaves tready low, so the BFM never
    // holds a beat the reader has no room for. A reader leaves receiveInfo()
    // only with a beat, so tready that is high on an edge with no transfer
    // stays high without a new sample.
    void bfm_driver_thread() {
        axi4StreamInfoSt<TDATA_T, TID_T, TDEST_T, TUSER_T> tinfo;
        bool sample = true;
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            if (sample) {
                wait(sc_get_time_resolution());
                hdl_if_p->tready = m_tx->get_rdy();
                if (!m_tx->get_rdy() && m_clock.waitReadyInClock(clk, m_tx->readEnteredEvent(), [this] { return m_tx->get_rdy(); })) {
                    hdl_if_p->tready = true;
                }
            }
            wait(clk.posedge_event());
            if (!(hdl_if_p->tvalid && hdl_if_p->tready)) {
                sample = !hdl_if_p->tready;
                continue;
            }
            sample = true;
            m_paced.transfer(sc_time_stamp(), m_tx->readEnteredTime(), m_tx->readEnteredDelta(),
                             m_tx->readEnteredProcess());
            // A beat sampled in reset is still delivered, but the monitor
            // counts only transfers out of reset.
            if (rst_n) {
                m_sampledBeats++;
                m_lastSampleTime = sc_time_stamp();
            }
            tinfo.tdata.sc_unpack(hdl_if_p->tdata);
            tinfo.tstrb.sc_unpack(hdl_if_p->tstrb);
            tinfo.tkeep.sc_unpack(hdl_if_p->tkeep);
            tinfo.tlast = (bool) hdl_if_p->tlast.read();;
            tinfo.tid.sc_unpack(hdl_if_p->tid);
            tinfo.tdest.sc_unpack(hdl_if_p->tdest);
            if constexpr (hasOptionalPayload<TUSER_T>) { tinfo.tuser.sc_unpack(hdl_if_p->tuser); }
            // A delayed write blocks across clock edges, and the HDL must not
            // transfer on them.
            hdl_if_p->tready = false;
            if_p->sendInfo(tinfo);
        }
    }

    // The driver wakes on the same edge in either order, so this checks the
    // beats sampled up to the previous edge before counting this edge.
    void transfer_monitor() {
        m_clock.rose();
        checkLostBeats(m_sampledBeats - (m_lastSampleTime == sc_time_stamp() ? 1 : 0));
        m_lastEdge = sc_time_stamp();
        m_paced.edge(m_lastEdge);
        if (!rst_n || !hdl_if_p->tvalid) {
            return;
        }
        if (hdl_if_p->tready) {
            m_hdlBeats++;
        } else if (m_noBackpressure) {
            m_scStalls.fail(sc_time_stamp());
        }
    }

    void clock_fall() {
        m_clock.fell();
    }

private:

    void checkLostBeats(uint64_t sampledBeats) {
        while (m_hdlBeats > sampledBeats + m_lostBeats.count_) {
            m_lostBeats.fail(m_lastEdge);
        }
    }

    bfmSameClockAnswer m_clock;
    axi4_stream_channel<TDATA_T, TID_T, TDEST_T, TUSER_T> * m_chnl;
    rdy_vld_channel<axi4StreamInfoSt<TDATA_T, TID_T, TDEST_T, TUSER_T>> * m_tx;
    bool m_noBackpressure = false;
    uint64_t m_hdlBeats = 0;
    uint64_t m_sampledBeats = 0;
    sc_time m_lastSampleTime;
    sc_time m_lastEdge;
    bfmContractCheck m_lostBeats;
    bfmContractCheck m_scStalls;
    bfmClockPaced m_paced;

};

template<typename TDATA_T, typename TID_T, typename TDEST_T,
typename VL_TDATA_T, typename VL_TID_T, typename VL_TDEST_T, typename VL_TSTRB_T, typename VL_TKEEP_T,
typename VL_TUSER_T = bool, typename TUSER_T = std::monostate>
class axi4_stream_dst_bfm: public sc_module {

public:

    axi4_stream_in<TDATA_T, TID_T, TDEST_T, TUSER_T> if_p;
    sc_port<axi4_stream_hdl_if<VL_TDATA_T, VL_TID_T, VL_TDEST_T, VL_TSTRB_T, VL_TKEEP_T, VL_TUSER_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi4_stream_dst_bfm);

    axi4_stream_dst_bfm(sc_module_name modulename) :
        m_stalls(name(), "HDL stalled a backpressure: false interface", "clock edges"),
        m_lowered(name()),
        m_paced(name()) {
        bfmClocks::add(if_p, clk, &m_clock);
        SC_THREAD(bfm_driver_thread);
        SC_METHOD(edge_monitor);
        sensitive << clk.pos();
        dont_initialize();
        SC_METHOD(clock_fall);
        sensitive << clk.neg();
        dont_initialize();
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi4_stream_channel<TDATA_T, TID_T, TDEST_T, TUSER_T> *>(if_p.get_interface());
        m_noBackpressure = bfmNoBackpressure(m_chnl->m_tx_out.get_interface(), name());
        if_p->setCycleTransaction(PORTTYPE_IN);
        m_tx = dynamic_cast<rdy_vld_channel<axi4StreamInfoSt<TDATA_T, TID_T, TDEST_T, TUSER_T>> *>(m_chnl->m_tx_in.get_interface());
        Q_ASSERT_CTX(m_tx != nullptr, name(), "axi4_stream channel does not carry its beats on a rdy_vld_channel");
        if_p->setExternalEvent(&m_offer);
        m_paced.port_ = m_chnl->name();
    }

    virtual void end_of_simulation() {
        m_stalls.report();
        m_lowered.report();
    }

    // A beat stays the writer's until the HDL is certain to take it. The BFM
    // shows the offered beat on the pins from a point in the clock's high
    // phase and reads it at the sample point before the edge that transfers
    // it (bfmSameClockAnswer::waitTaken()), so the writer blocks as it would
    // on the RTL's output register and the BFM holds no beat of its own. A
    // beat whose tready falls after that read is held on the pins until the
    // HDL takes it, as the writer's would have been.
    void bfm_driver_thread() {
        axi4StreamInfoSt<TDATA_T, TID_T, TDEST_T, TUSER_T> tinfo;
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        m_clock.rose();
        while (true) {
            hdl_if_p->tvalid = 0;
            hdl_if_p->tdata = VL_TDATA_T(0);
            hdl_if_p->tstrb = VL_TDATA_T(0);
            hdl_if_p->tkeep = VL_TDATA_T(0);
            hdl_if_p->tlast = 0;
            hdl_if_p->tid = VL_TID_T(0);
            hdl_if_p->tdest = VL_TDEST_T(0);
            if constexpr (hasOptionalPayload<TUSER_T>) { hdl_if_p->tuser = VL_TUSER_T(0); }
            while (!m_tx->offered(tinfo)) {
                wait(m_offer);
            }
            m_clock.waitDrivePoint(clk);
            hdl_if_p->tvalid = 1;
            hdl_if_p->tdata = tinfo.tdata.sc_pack();
            hdl_if_p->tstrb = tinfo.tstrb.sc_pack();
            hdl_if_p->tkeep = tinfo.tkeep.sc_pack();
            hdl_if_p->tlast = tinfo.tlast;
            hdl_if_p->tid = tinfo.tid.sc_pack();
            hdl_if_p->tdest = tinfo.tdest.sc_pack();
            if constexpr (hasOptionalPayload<TUSER_T>) { hdl_if_p->tuser = tinfo.tuser.sc_pack(); }
            const sc_time writeTime = m_tx->writeEnteredTime();
            const sc_dt::uint64 writeDelta = m_tx->writeEnteredDelta();
            const sc_object *writer = m_tx->writeEnteredProcess();
            auto tready = [this] { return hdl_if_p->tready.read(); };
            const bool certain = m_clock.waitTaken(clk, tready, [this] {
                if (m_noBackpressure && rst_n && !hdl_if_p->tready) {
                    m_stalls.fail(sc_time_stamp());
                }
            });
            if_p->receiveInfo(tinfo);
            if (certain && !m_clock.waitTakenEdge(clk, rst_n, tready, m_lowered)) {
                do {
                    wait(clk.posedge_event());
                    m_clock.rose();
                } while (!hdl_if_p->tready);
            }
            m_paced.transfer(sc_time_stamp(), writeTime, writeDelta, writer);
        }
    }

    void edge_monitor() {
        m_clock.rose();
        m_paced.edge(sc_time_stamp());
    }

    void clock_fall() {
        m_clock.fell();
    }

private:

    axi4_stream_channel<TDATA_T, TID_T, TDEST_T, TUSER_T> * m_chnl;
    rdy_vld_channel<axi4StreamInfoSt<TDATA_T, TID_T, TDEST_T, TUSER_T>> * m_tx;
    sc_event m_offer;
    bool m_noBackpressure = false;
    bfmContractCheck m_stalls;
    bfmReadyLowered m_lowered;
    bfmClockPaced m_paced;
    bfmSameClockAnswer m_clock;

};
#endif /* AXI4_STREAM_BFM_H_ */
