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
        m_scStalls(name(), "SystemC stalled a backpressure: false producer", "clock edges") {
        SC_THREAD(bfm_driver_thread);
        SC_METHOD(transfer_monitor);
        sensitive << clk.pos();
        dont_initialize();
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi4_stream_channel<TDATA_T, TID_T, TDEST_T, TUSER_T> *>(if_p.get_interface());
        m_noBackpressure = bfmNoBackpressure(m_chnl->m_tx_out.get_interface(), name());
        if_p->setCycleTransaction(PORTTYPE_OUT);
    }

    virtual void end_of_simulation() {
        checkLostBeats(m_sampledBeats);
        m_lostBeats.report();
        m_scStalls.report();
    }

    void bfm_driver_thread() {
        axi4StreamInfoSt<TDATA_T, TID_T, TDEST_T, TUSER_T> tinfo;
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            bool tready = m_chnl->m_tx_out->get_rdy();
            hdl_if_p->tready = tready;
            while (!(hdl_if_p->tvalid && hdl_if_p->tready)) {
                wait(clk.posedge_event());
                tready = m_chnl->m_tx_out->get_rdy();
                hdl_if_p->tready = tready;
            }
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
            // transfer on them. A write that returns in this timestep leaves
            // the next edge the tready it would have seen without the write.
            hdl_if_p->tready = false;
            if_p->sendInfo(tinfo);
            hdl_if_p->tready = tready;
            wait(clk.posedge_event());
        }
    }

    // The driver wakes on the same edge in either order, so this checks the
    // beats sampled up to the previous edge before counting this edge.
    void transfer_monitor() {
        checkLostBeats(m_sampledBeats - (m_lastSampleTime == sc_time_stamp() ? 1 : 0));
        m_lastEdge = sc_time_stamp();
        if (!rst_n || !hdl_if_p->tvalid) {
            return;
        }
        if (hdl_if_p->tready) {
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

    axi4_stream_channel<TDATA_T, TID_T, TDEST_T, TUSER_T> * m_chnl;
    bool m_noBackpressure = false;
    uint64_t m_hdlBeats = 0;
    uint64_t m_sampledBeats = 0;
    sc_time m_lastSampleTime;
    sc_time m_lastEdge;
    bfmContractCheck m_lostBeats;
    bfmContractCheck m_scStalls;

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
        m_stalls(name(), "HDL stalled a backpressure: false interface", "clock edges") {
        SC_THREAD(bfm_driver_thread);
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi4_stream_channel<TDATA_T, TID_T, TDEST_T, TUSER_T> *>(if_p.get_interface());
        m_noBackpressure = bfmNoBackpressure(m_chnl->m_tx_out.get_interface(), name());
        if_p->setCycleTransaction(PORTTYPE_IN);
    }

    virtual void end_of_simulation() {
        m_stalls.report();
    }

    void bfm_driver_thread() {
        axi4StreamInfoSt<TDATA_T, TID_T, TDEST_T, TUSER_T> tinfo;
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            hdl_if_p->tvalid = 0;
            hdl_if_p->tdata = VL_TDATA_T(0);
            hdl_if_p->tstrb = VL_TDATA_T(0);
            hdl_if_p->tkeep = VL_TDATA_T(0);
            hdl_if_p->tlast = 0;
            hdl_if_p->tid = VL_TID_T(0);
            hdl_if_p->tdest = VL_TDEST_T(0);
            if constexpr (hasOptionalPayload<TUSER_T>) { hdl_if_p->tuser = VL_TUSER_T(0); }
            if_p->receiveInfo(tinfo);
            hdl_if_p->tvalid = 1;
            hdl_if_p->tdata = tinfo.tdata.sc_pack();
            hdl_if_p->tstrb = tinfo.tstrb.sc_pack();
            hdl_if_p->tkeep = tinfo.tkeep.sc_pack();
            hdl_if_p->tlast = tinfo.tlast;
            hdl_if_p->tid = tinfo.tid.sc_pack();
            hdl_if_p->tdest = tinfo.tdest.sc_pack();
            if constexpr (hasOptionalPayload<TUSER_T>) { hdl_if_p->tuser = tinfo.tuser.sc_pack(); }
            do {
                wait(clk.posedge_event());
                if (m_noBackpressure && rst_n && !hdl_if_p->tready) {
                    m_stalls.fail(sc_time_stamp());
                }
            } while (!hdl_if_p->tready);
        }
    }

private:

    axi4_stream_channel<TDATA_T, TID_T, TDEST_T, TUSER_T> * m_chnl;
    bool m_noBackpressure = false;
    bfmContractCheck m_stalls;

};
#endif /* AXI4_STREAM_BFM_H_ */
