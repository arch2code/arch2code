#ifndef AXI4_STREAM_BFM_H_
#define AXI4_STREAM_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "axi4_stream_channel.h"

template<typename VL_TDATA_T, typename VL_TID_T, typename VL_TDEST_T, typename VL_TUSER_T, typename VL_TSTRB_T, typename VL_TKEEP_T>
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

template<typename TDATA_T, typename TID_T, typename TDEST_T, typename TUSER_T,
typename VL_TDATA_T, typename VL_TID_T, typename VL_TDEST_T, typename VL_TUSER_T, typename VL_TSTRB_T, typename VL_TKEEP_T>
class axi4_stream_src_bfm: public sc_module {

public:

    axi4_stream_out<TDATA_T, TID_T, TDEST_T, TUSER_T> if_p;
    sc_port<axi4_stream_hdl_if<VL_TDATA_T, VL_TID_T, VL_TDEST_T, VL_TUSER_T, VL_TSTRB_T, VL_TKEEP_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi4_stream_src_bfm);

    axi4_stream_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi4_stream_channel<TDATA_T, TID_T, TDEST_T, TUSER_T> *>(if_p.get_interface());
        if_p->setCycleTransaction(PORTTYPE_OUT);
    }

    void bfm_driver_thread() {
        axi4StreamInfoSt<TDATA_T, TID_T, TDEST_T, TUSER_T> tinfo;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->tready = m_chnl->m_tx_out->get_rdy();
            while (!(hdl_if_p->tvalid && hdl_if_p->tready)) {
                wait(clk.posedge_event());
                hdl_if_p->tready = m_chnl->m_tx_out->get_rdy();
            }
            tinfo.tdata.sc_unpack(hdl_if_p->tdata);
            tinfo.tstrb.sc_unpack(hdl_if_p->tstrb);
            tinfo.tkeep.sc_unpack(hdl_if_p->tkeep);
            tinfo.tlast = (bool) hdl_if_p->tlast.read();;
            tinfo.tid.sc_unpack(hdl_if_p->tid);
            tinfo.tdest.sc_unpack(hdl_if_p->tdest);
            tinfo.tuser.sc_unpack(hdl_if_p->tuser);
            if_p->sendInfo(tinfo);
            wait(clk.posedge_event());
        }
    }

private:

    axi4_stream_channel<TDATA_T, TID_T, TDEST_T, TUSER_T> * m_chnl;

};

template<typename TDATA_T, typename TID_T, typename TDEST_T, typename TUSER_T,
typename VL_TDATA_T, typename VL_TID_T, typename VL_TDEST_T, typename VL_TUSER_T, typename VL_TSTRB_T, typename VL_TKEEP_T>
class axi4_stream_dst_bfm: public sc_module {

public:

    axi4_stream_in<TDATA_T, TID_T, TDEST_T, TUSER_T> if_p;
    sc_port<axi4_stream_hdl_if<VL_TDATA_T, VL_TID_T, VL_TDEST_T, VL_TUSER_T, VL_TSTRB_T, VL_TKEEP_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi4_stream_dst_bfm);

    axi4_stream_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi4_stream_channel<TDATA_T, TID_T, TDEST_T, TUSER_T> *>(if_p.get_interface());
        if_p->setCycleTransaction(PORTTYPE_IN);
    }

    void bfm_driver_thread() {
        axi4StreamInfoSt<TDATA_T, TID_T, TDEST_T, TUSER_T> tinfo;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->tvalid = 0;
            hdl_if_p->tdata = VL_TDATA_T(0);
            hdl_if_p->tstrb = VL_TDATA_T(0);
            hdl_if_p->tkeep = VL_TDATA_T(0);
            hdl_if_p->tlast = 0;
            hdl_if_p->tid = VL_TID_T(0);
            hdl_if_p->tdest = VL_TDEST_T(0);
            hdl_if_p->tuser = VL_TUSER_T(0);
            if_p->receiveInfo(tinfo);
            hdl_if_p->tvalid = 1;
            hdl_if_p->tdata = tinfo.tdata.sc_pack();
            hdl_if_p->tstrb = tinfo.tstrb.sc_pack();
            hdl_if_p->tkeep = tinfo.tkeep.sc_pack();
            hdl_if_p->tlast = tinfo.tlast;
            hdl_if_p->tid = tinfo.tid.sc_pack();
            hdl_if_p->tdest = tinfo.tdest.sc_pack();
            hdl_if_p->tuser = tinfo.tuser.sc_pack();
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->tready);
        }
    }

private:

    axi4_stream_channel<TDATA_T, TID_T, TDEST_T, TUSER_T> * m_chnl;

};
#endif /* AXI4_STREAM_BFM_H_ */
