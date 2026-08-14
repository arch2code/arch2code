#ifndef AXI_WRITE_BFM_H_
#define AXI_WRITE_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "axi_write_channel.h"
#include "optionalPayload.h"

// The AWUSER, WUSER and BUSER sidebands are optional, so both of each one's
// template arguments sit in the argument tail: the payload type (AWU, WU, BU)
// and the Verilated bridge type (VL_AWUSER_T, VL_WUSER_T, VL_BUSER_T). Each
// user signal is a real interface signal, so the HDL boundary keeps a port for
// it whether or not a payload is bound. When none is, the bridge type defaults
// to the one-bit placeholder the SystemVerilog interface declares and nothing
// ever drives or samples it.
template<typename VL_ADDR_T, typename VL_DATA_T, typename VL_STRB_T,
typename VL_AWUSER_T = bool, typename VL_WUSER_T = bool, typename VL_BUSER_T = bool>
struct axi_write_hdl_if: public sc_interface {

    static constexpr unsigned int idWidth    = 4;
    static constexpr unsigned int lenWidth   = 8;
    static constexpr unsigned int sizeWidth  = 3;
    static constexpr unsigned int burstWidth = 2;
    static constexpr unsigned int respWidth = 2;

    sc_signal<sc_bv<idWidth>> awid;
    sc_signal<VL_ADDR_T> awaddr;
    sc_signal<sc_bv<lenWidth>> awlen;
    sc_signal<sc_bv<sizeWidth>> awsize;
    sc_signal<sc_bv<burstWidth>> awburst;
    sc_signal<VL_AWUSER_T> awuser;
    sc_signal<bool> awvalid;
    sc_signal<bool> awready;

    sc_signal<sc_bv<idWidth>> wid;
    sc_signal<VL_DATA_T> wdata;
    sc_signal<VL_STRB_T> wstrb;
    sc_signal<bool> wlast;
    sc_signal<VL_WUSER_T> wuser;
    sc_signal<bool> wvalid;
    sc_signal<bool> wready;

    sc_signal<sc_bv<idWidth>> bid;
    sc_signal<sc_bv<respWidth>> bresp;
    sc_signal<VL_BUSER_T> buser;
    sc_signal<bool> bvalid;
    sc_signal<bool> bready;

};

template<typename ADDR_T, typename DATA_T, typename STRB_T, typename VL_ADDR_T, typename VL_DATA_T, typename VL_STRB_T,
         typename VL_AWUSER_T = bool, typename VL_WUSER_T = bool, typename VL_BUSER_T = bool,
         typename AWU = std::monostate, typename WU = std::monostate, typename BU = std::monostate>
class axi_write_src_bfm: public sc_module {

public:

    axi_write_out<ADDR_T, DATA_T, STRB_T, AWU, WU, BU> if_p;
    sc_port<axi_write_hdl_if<VL_ADDR_T, VL_DATA_T, VL_STRB_T, VL_AWUSER_T, VL_WUSER_T, VL_BUSER_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi_write_src_bfm);

    axi_write_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_aw_thread);
        SC_THREAD(bfm_driver_w_thread);
        SC_THREAD(bfm_driver_b_thread);
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi_write_channel<ADDR_T, DATA_T, STRB_T, AWU, WU, BU> *>(if_p.get_interface());
        if_p->setCycleTransaction(PORTTYPE_OUT);
    }

    void bfm_driver_aw_thread() {
        axiWriteAddressSt<ADDR_T, AWU> aw_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->awready = m_chnl->m_addr_out->get_rdy();
            while (!(hdl_if_p->awvalid && hdl_if_p->awready)) {
                wait(clk.posedge_event());
                hdl_if_p->awready = m_chnl->m_addr_out->get_rdy();
            }
            aw_data.awid = (_axiIdT) hdl_if_p->awid.read().to_uint();
            aw_data.awaddr.sc_unpack(hdl_if_p->awaddr);
            aw_data.awlen = (uint8_t) hdl_if_p->awlen.read().to_uint();
            aw_data.awsize = (_axiSizeT) hdl_if_p->awsize.read().to_uint();
            aw_data.awburst = (_axiBurstT) hdl_if_p->awburst.read().to_uint();
            if constexpr (hasOptionalPayload<AWU>) { aw_data.user.sc_unpack(hdl_if_p->awuser); }
            if_p->sendAddr(aw_data);
            wait(clk.posedge_event());
        }
    }

    void bfm_driver_w_thread() {
        axiWriteDataSt<DATA_T, STRB_T, WU> w_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->wready = m_chnl->m_data_out->get_rdy();
            while (!(hdl_if_p->wvalid && hdl_if_p->wready)) {
                wait(clk.posedge_event());
                hdl_if_p->wready = m_chnl->m_data_out->get_rdy();
            }
            w_data.wid = (_axiIdT) hdl_if_p->wid.read().to_uint();
            w_data.wdata.sc_unpack(hdl_if_p->wdata);
            w_data.wstrb.sc_unpack(hdl_if_p->wstrb);
            w_data.wlast = (bool) hdl_if_p->wlast.read();
            if constexpr (hasOptionalPayload<WU>) { w_data.user.sc_unpack(hdl_if_p->wuser); }
            if_p->sendDataCycle(w_data);
            wait(clk.posedge_event());
        }
    }

    void bfm_driver_b_thread() {
        axiWriteRespSt<BU> b_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->bvalid = 0;
            hdl_if_p->bid = 0;
            hdl_if_p->bresp = 0;
            if constexpr (hasOptionalPayload<BU>) { hdl_if_p->buser = VL_BUSER_T(0); }
            if_p->receiveRespCycle(b_data);
            hdl_if_p->bvalid = 1;
            hdl_if_p->bid = b_data.bid;
            hdl_if_p->bresp = b_data.bresp;
            if constexpr (hasOptionalPayload<BU>) { hdl_if_p->buser = b_data.user.sc_pack(); }
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->bready);
        }
    }

private:

    axi_write_channel<ADDR_T, DATA_T, STRB_T, AWU, WU, BU> * m_chnl;

};

template<typename ADDR_T, typename DATA_T, typename STRB_T, typename VL_ADDR_T, typename VL_DATA_T, typename VL_STRB_T,
         typename VL_AWUSER_T = bool, typename VL_WUSER_T = bool, typename VL_BUSER_T = bool,
         typename AWU = std::monostate, typename WU = std::monostate, typename BU = std::monostate>
class axi_write_dst_bfm: public sc_module {

public:

    axi_write_in<ADDR_T, DATA_T, STRB_T, AWU, WU, BU> if_p;
    sc_port<axi_write_hdl_if<VL_ADDR_T, VL_DATA_T, VL_STRB_T, VL_AWUSER_T, VL_WUSER_T, VL_BUSER_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi_write_dst_bfm);

    axi_write_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_aw_thread);
        SC_THREAD(bfm_driver_w_thread);
        SC_THREAD(bfm_driver_b_thread);
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi_write_channel<ADDR_T, DATA_T, STRB_T, AWU, WU, BU> *>(if_p.get_interface());
        if_p->setCycleTransaction(PORTTYPE_IN);
    }

    void bfm_driver_aw_thread() {
        axiWriteAddressSt<ADDR_T, AWU> aw_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->awvalid = 0;
            hdl_if_p->awid = 0;
            hdl_if_p->awaddr = VL_ADDR_T(0);
            hdl_if_p->awlen = 0;
            hdl_if_p->awsize = 0;
            hdl_if_p->awburst = 0;
            if constexpr (hasOptionalPayload<AWU>) { hdl_if_p->awuser = VL_AWUSER_T(0); }
            if_p->receiveAddr(aw_data);
            hdl_if_p->awvalid = 1;
            hdl_if_p->awid = aw_data.awid;
            hdl_if_p->awaddr = aw_data.awaddr.sc_pack();
            hdl_if_p->awlen = aw_data.awlen;
            hdl_if_p->awsize = aw_data.awsize;
            hdl_if_p->awburst = aw_data.awburst;
            if constexpr (hasOptionalPayload<AWU>) { hdl_if_p->awuser = aw_data.user.sc_pack(); }
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->awready);
        }
    }

    void bfm_driver_w_thread() {
        axiWriteDataSt<DATA_T, STRB_T, WU> w_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->wvalid = 0;
            hdl_if_p->wid = 0;
            hdl_if_p->wdata = VL_DATA_T(0);
            hdl_if_p->wstrb = VL_STRB_T(0);
            hdl_if_p->wlast = 0;
            if constexpr (hasOptionalPayload<WU>) { hdl_if_p->wuser = VL_WUSER_T(0); }
            if_p->receiveDataCycle(w_data);
            hdl_if_p->wvalid = 1;
            hdl_if_p->wid = w_data.wid;
            hdl_if_p->wdata = w_data.wdata.sc_pack();
            hdl_if_p->wstrb = w_data.wstrb.sc_pack();
            hdl_if_p->wlast = w_data.wlast;
            if constexpr (hasOptionalPayload<WU>) { hdl_if_p->wuser = w_data.user.sc_pack(); }
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->awready);
        }
    }

    void bfm_driver_b_thread() {
        axiWriteRespSt<BU> b_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->bready = m_chnl->m_resp_out->get_rdy();
            while (!(hdl_if_p->bvalid && hdl_if_p->bready)) {
                wait(clk.posedge_event());
                hdl_if_p->bready = m_chnl->m_resp_out->get_rdy();
            }
            b_data.bid = (_axiIdT) hdl_if_p->bid.read().to_uint();
            b_data.bresp = (_axiResponseT) hdl_if_p->bresp.read().to_uint();
            if constexpr (hasOptionalPayload<BU>) { b_data.user.sc_unpack(hdl_if_p->buser); }
            if_p->sendRespCycle(b_data);
            wait(clk.posedge_event());
        }
    }

private:

    axi_write_channel<ADDR_T, DATA_T, STRB_T, AWU, WU, BU> * m_chnl;

};

#endif /* AXI_WRITE_BFM_H_ */
