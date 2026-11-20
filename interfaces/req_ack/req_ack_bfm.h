#ifndef REQ_ACK_BFM_H_
#define REQ_ACK_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "bfmClockEdge.h"
#include "req_ack_channel.h"

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
    bfmClockEdge m_edge{"clk_edge"};

    SC_HAS_PROCESS (req_ack_src_bfm);

    req_ack_src_bfm(sc_module_name modulename) {
        m_edge.clk(clk);
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        DATA_T data;
        RDATA_T rdata;
        while (true) {
            hdl_if_p->ack = false;
            hdl_if_p->rdata = VL_RDATA_T(0);
            // A request the RTL raised at a rising edge has settled by the
            // falling edge, so the model gets it there and its ack is on the
            // wire for the next rising edge. A rising edge still catches a
            // request raised after the falling edge. No request is taken
            // while reset is asserted.
            do {
                wait(clk.posedge_event() | clk.negedge_event());
            } while (!hdl_if_p->req || !rst_n);
            data.sc_unpack(hdl_if_p->data);
            if_p->req(data, rdata);
            m_edge.settle();
            hdl_if_p->ack = true;
            hdl_if_p->rdata = rdata.sc_pack();
            wait(clk.posedge_event());
        }
    }

};

template<typename DATA_T, typename RDATA_T, typename VL_DATA_T, typename VL_RDATA_T>
class req_ack_dst_bfm: public sc_module {

public:

    req_ack_in<DATA_T, RDATA_T> if_p;
    sc_port<req_ack_hdl_if<VL_DATA_T, VL_RDATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;
    bfmClockEdge m_edge{"clk_edge"};

    SC_HAS_PROCESS (req_ack_dst_bfm);

    req_ack_dst_bfm(sc_module_name modulename) {
        m_edge.clk(clk);
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            DATA_T data;
            RDATA_T rdata;
            if_p->reqReceive(data);
            m_edge.settle();
            hdl_if_p->req = true;
            hdl_if_p->data = data.sc_pack();
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->ack);
            rdata.sc_unpack(hdl_if_p->rdata);
            // Drop req before a delayed ack() blocks, as push_ack_dst_bfm drops push.
            hdl_if_p->req = false;
            if_p->ack(rdata);
        }
    }

};

#endif /* REQ_ACK_BFM_H_ */
