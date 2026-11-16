#ifndef AXI_READ_BFM_H_
#define AXI_READ_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "axi_read_channel.h"
#include "optionalPayload.h"
#include "q_assert.h"

// The ARUSER and RUSER sidebands are optional, so both of each one's template
// arguments sit in the argument tail: the payload type (ARU, RU) and the
// Verilated bridge type (VL_ARUSER_T, VL_RUSER_T). Each user signal is a real
// interface signal, so the HDL boundary keeps a port for it whether or not a
// payload is bound. When none is, the bridge type defaults to the one-bit
// placeholder the SystemVerilog interface declares and nothing ever drives or
// samples it. id_t is optional too, so the ARID/RID bridge type VL_ID_T sits
// after the USER bridge types, defaulting to the 4-bit vector the SystemVerilog
// interface declares when id_t is left unbound; the ID payload type and its
// bit width sit last, defaulting to _axiIdT and 4.
template<typename VL_ADDR_T, typename VL_DATA_T,
typename VL_ARUSER_T = bool, typename VL_RUSER_T = bool, typename VL_ID_T = sc_bv<4>>
struct axi_read_hdl_if: public sc_interface {

    static constexpr unsigned int lenWidth   = 8;
    static constexpr unsigned int sizeWidth  = 3;
    static constexpr unsigned int burstWidth = 2;
    static constexpr unsigned int respWidth = 2;

    sc_signal<VL_ID_T> arid;
    sc_signal<VL_ADDR_T> araddr;
    sc_signal<sc_bv<lenWidth>> arlen;
    sc_signal<sc_bv<sizeWidth>> arsize;
    sc_signal<sc_bv<burstWidth>> arburst;
    sc_signal<VL_ARUSER_T> aruser;
    sc_signal<bool> arvalid;
    sc_signal<bool> arready;

    sc_signal<VL_ID_T> rid;
    sc_signal<VL_DATA_T> rdata;
    sc_signal<bool> rlast;
    sc_signal<sc_bv<respWidth>> rresp;
    sc_signal<VL_RUSER_T> ruser;
    sc_signal<bool> rvalid;
    sc_signal<bool> rready;

};

// Each AXI channel is a rdy_vld channel, and the BFMs keep the exact
// handshake of the rdy_vld BFMs on every one of them. Where the HDL sends,
// the ready pin is driven one time resolution step after a rising edge, once
// the model's zero-time work at that edge is done, from whether the model
// waits to receive; it is driven after each transfer and on every edge while
// it is low, and lowered on a transfer, so the BFM never takes a beat the
// model has no room for. Where the model sends, the BFM shows the beat the
// model offers on the pins and reads it on the edge the HDL transfers it, so
// the model's send returns on that edge. Either way the BFM holds no beat of
// its own.
template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T,
         typename VL_ARUSER_T = bool, typename VL_RUSER_T = bool, typename VL_ID_T = sc_bv<4>,
         typename ARU = std::monostate, typename RU = std::monostate, typename ID = _axiIdT, unsigned IDW = 4>
class axi_read_src_bfm: public sc_module {

public:

    axi_read_out<ADDR_T, DATA_T, ARU, RU, ID, IDW> if_p;
    sc_port<axi_read_hdl_if<VL_ADDR_T, VL_DATA_T, VL_ARUSER_T, VL_RUSER_T, VL_ID_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi_read_src_bfm);

    axi_read_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_ar_thread);
        SC_THREAD(bfm_driver_r_thread);
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi_read_channel<ADDR_T, DATA_T, ARU, RU, ID, IDW> *>(if_p.get_interface());
        Q_ASSERT_CTX(m_chnl != nullptr, name(), "BFM is bound to an interface that is not an axi_read_channel");
        if_p->setCycleTransaction(PORTTYPE_OUT);
        m_r = dynamic_cast<rdy_vld_channel<axiReadRespSt<DATA_T, RU, ID, IDW>> *>(m_chnl->m_data_in.get_interface());
        Q_ASSERT_CTX(m_r != nullptr, name(), "axi_read channel does not carry R on a rdy_vld_channel");
        m_r->setExternalEvent(&m_rOffer);
    }

    void bfm_driver_ar_thread() {
        axiReadAddressSt<ADDR_T, ARU, ID, IDW> ar_data;
        bool sample = true;
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            if (sample) {
                wait(sc_get_time_resolution());
                hdl_if_p->arready = m_chnl->m_addr_out->get_rdy();
            }
            wait(clk.posedge_event());
            if (!rst_n.read()) {
                hdl_if_p->arready = 0;
                while (!rst_n.read()) {
                    wait(clk.posedge_event());
                }
                sample = true;
                continue;
            }
            if (!(hdl_if_p->arvalid && hdl_if_p->arready)) {
                sample = !hdl_if_p->arready;
                continue;
            }
            sample = true;
            ar_data.arid = (ID) hdl_if_p->arid.read().to_uint();
            ar_data.araddr.sc_unpack(hdl_if_p->araddr);
            ar_data.arlen = (uint8_t) hdl_if_p->arlen.read().to_uint();
            ar_data.arsize = (_axiSizeT) hdl_if_p->arsize.read().to_uint();
            ar_data.arburst = (_axiBurstT) hdl_if_p->arburst.read().to_uint();
            if constexpr (hasOptionalPayload<ARU>) { ar_data.user.sc_unpack(hdl_if_p->aruser); }
            // A delayed send blocks across clock edges, and the HDL must not
            // transfer on them.
            hdl_if_p->arready = false;
            if_p->sendAddr(ar_data);
        }
    }

    // During ARESETn the port_socket drains outstanding AR with dummy beats.
    // The BFM takes them at once and drives none, as the DUT ignores R in
    // reset; a beat waiting on the pins when reset asserts is dropped too.
    void bfm_driver_r_thread() {
        axiReadRespSt<DATA_T, RU, ID, IDW> r_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->rvalid = 0;
            hdl_if_p->rid = VL_ID_T(0);
            hdl_if_p->rdata = VL_DATA_T(0);
            hdl_if_p->rresp = 0;
            hdl_if_p->rlast = 0;
            if constexpr (hasOptionalPayload<RU>) { hdl_if_p->ruser = VL_RUSER_T(0); }
            while (!m_r->offered(r_data)) {
                wait(m_rOffer);
            }
            if (!rst_n.read()) {
                if_p->receiveDataCycle(r_data);
                continue;
            }
            hdl_if_p->rvalid = 1;
            hdl_if_p->rid = r_data.rid;
            hdl_if_p->rdata = r_data.rdata.sc_pack();
            hdl_if_p->rresp = r_data.rresp;
            hdl_if_p->rlast = r_data.rlast;
            if constexpr (hasOptionalPayload<RU>) { hdl_if_p->ruser = r_data.user.sc_pack(); }
            do {
                wait(clk.posedge_event());
            } while (rst_n.read() && !hdl_if_p->rready);
            if_p->receiveDataCycle(r_data);
        }
    }

private:

    axi_read_channel<ADDR_T, DATA_T, ARU, RU, ID, IDW> * m_chnl = nullptr;
    rdy_vld_channel<axiReadRespSt<DATA_T, RU, ID, IDW>> * m_r = nullptr;
    sc_event m_rOffer;

};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T,
         typename VL_ARUSER_T = bool, typename VL_RUSER_T = bool, typename VL_ID_T = sc_bv<4>,
         typename ARU = std::monostate, typename RU = std::monostate, typename ID = _axiIdT, unsigned IDW = 4>
class axi_read_dst_bfm: public sc_module {

public:

    axi_read_in<ADDR_T, DATA_T, ARU, RU, ID, IDW> if_p;
    sc_port<axi_read_hdl_if<VL_ADDR_T, VL_DATA_T, VL_ARUSER_T, VL_RUSER_T, VL_ID_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi_read_dst_bfm);

    axi_read_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_ar_thread);
        SC_THREAD(bfm_driver_r_thread);
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi_read_channel<ADDR_T, DATA_T, ARU, RU, ID, IDW> *>(if_p.get_interface());
        Q_ASSERT_CTX(m_chnl != nullptr, name(), "BFM is bound to an interface that is not an axi_read_channel");
        if_p->setCycleTransaction(PORTTYPE_IN);
        m_ar = dynamic_cast<rdy_vld_channel<axiReadAddressSt<ADDR_T, ARU, ID, IDW>> *>(m_chnl->m_addr_in.get_interface());
        Q_ASSERT_CTX(m_ar != nullptr, name(), "axi_read channel does not carry AR on a rdy_vld_channel");
        m_ar->setExternalEvent(&m_arOffer);
    }

    void bfm_driver_ar_thread() {
        axiReadAddressSt<ADDR_T, ARU, ID, IDW> ar_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->arvalid = 0;
            hdl_if_p->arid = VL_ID_T(0);
            hdl_if_p->araddr = VL_ADDR_T(0);
            hdl_if_p->arlen = 0;
            hdl_if_p->arsize = 0;
            hdl_if_p->arburst = 0;
            if constexpr (hasOptionalPayload<ARU>) { hdl_if_p->aruser = VL_ARUSER_T(0); }
            while (!m_ar->offered(ar_data)) {
                wait(m_arOffer);
            }
            hdl_if_p->arvalid = 1;
            hdl_if_p->arid = ar_data.arid;
            hdl_if_p->araddr = ar_data.araddr.sc_pack();
            hdl_if_p->arlen = ar_data.arlen;
            hdl_if_p->arsize = ar_data.arsize;
            hdl_if_p->arburst = ar_data.arburst;
            if constexpr (hasOptionalPayload<ARU>) { hdl_if_p->aruser = ar_data.user.sc_pack(); }
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->arready);
            if_p->receiveAddr(ar_data);
        }
    }

    void bfm_driver_r_thread() {
        axiReadRespSt<DATA_T, RU, ID, IDW> r_data;
        bool sample = true;
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            if (sample) {
                wait(sc_get_time_resolution());
                hdl_if_p->rready = m_chnl->m_data_out->get_rdy();
            }
            wait(clk.posedge_event());
            if (!(hdl_if_p->rvalid && hdl_if_p->rready)) {
                sample = !hdl_if_p->rready;
                continue;
            }
            sample = true;
            r_data.rid = (ID) hdl_if_p->rid.read().to_uint();
            r_data.rdata.sc_unpack(hdl_if_p->rdata);
            r_data.rresp = (_axiResponseT) hdl_if_p->rresp.read().to_uint();
            r_data.rlast = (bool) hdl_if_p->rlast.read();
            if constexpr (hasOptionalPayload<RU>) { r_data.user.sc_unpack(hdl_if_p->ruser); }
            hdl_if_p->rready = false;
            if_p->sendDataCycle(r_data);
        }
    }

private:

    axi_read_channel<ADDR_T, DATA_T, ARU, RU, ID, IDW> * m_chnl = nullptr;
    rdy_vld_channel<axiReadAddressSt<ADDR_T, ARU, ID, IDW>> * m_ar = nullptr;
    sc_event m_arOffer;

};

#endif /* AXI_READ_BFM_H_ */
