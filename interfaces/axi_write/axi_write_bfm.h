#ifndef AXI_WRITE_BFM_H_
#define AXI_WRITE_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "axi_write_channel.h"
#include "optionalPayload.h"
#include "bfmContractCheck.h"
#include "q_assert.h"

#include <mutex>

// The AWUSER, WUSER and BUSER sidebands are optional, so both of each one's
// template arguments sit in the argument tail: the payload type (AWU, WU, BU)
// and the Verilated bridge type (VL_AWUSER_T, VL_WUSER_T, VL_BUSER_T). Each
// user signal is a real interface signal, so the HDL boundary keeps a port for
// it whether or not a payload is bound. When none is, the bridge type defaults
// to the one-bit placeholder the SystemVerilog interface declares and nothing
// ever drives or samples it. id_t is optional too, so the AWID/WID/BID bridge
// type VL_ID_T sits after the USER bridge types, defaulting to the 4-bit
// vector the SystemVerilog interface declares when id_t is left unbound; the
// ID payload type and its bit width sit last, defaulting to _axiIdT and 4.
template<typename VL_ADDR_T, typename VL_DATA_T, typename VL_STRB_T,
typename VL_AWUSER_T = bool, typename VL_WUSER_T = bool, typename VL_BUSER_T = bool, typename VL_ID_T = sc_bv<4>>
struct axi_write_hdl_if: public sc_interface {

    static constexpr unsigned int lenWidth   = 8;
    static constexpr unsigned int sizeWidth  = 3;
    static constexpr unsigned int burstWidth = 2;
    static constexpr unsigned int respWidth = 2;

    sc_signal<VL_ID_T> awid;
    sc_signal<VL_ADDR_T> awaddr;
    sc_signal<sc_bv<lenWidth>> awlen;
    sc_signal<sc_bv<sizeWidth>> awsize;
    sc_signal<sc_bv<burstWidth>> awburst;
    sc_signal<VL_AWUSER_T> awuser;
    sc_signal<bool> awvalid;
    sc_signal<bool> awready;

    sc_signal<VL_ID_T> wid;
    sc_signal<VL_DATA_T> wdata;
    sc_signal<VL_STRB_T> wstrb;
    sc_signal<bool> wlast;
    sc_signal<VL_WUSER_T> wuser;
    sc_signal<bool> wvalid;
    sc_signal<bool> wready;

    sc_signal<VL_ID_T> bid;
    sc_signal<sc_bv<respWidth>> bresp;
    sc_signal<VL_BUSER_T> buser;
    sc_signal<bool> bvalid;
    sc_signal<bool> bready;

};

// Each AXI channel is a rdy_vld channel, and the BFMs keep the exact
// handshake of the rdy_vld BFMs on every one of them. Where the HDL sends,
// the ready pin is driven one time resolution step after a rising edge, once
// the model's zero-time work at that edge is done, from whether the model
// waits to receive, or later in the clock while it is high if the model
// starts to receive then; it is driven after each transfer and on every edge
// while it is low, and lowered on a transfer, so the BFM never takes a beat
// the model has no room for. Where the model sends, the BFM shows the beat
// the model offers on the pins from a point in the clock's high phase and
// reads it at the sample point before the edge the HDL transfers it
// (bfmSameClockAnswer::waitTaken()), so the model's send returns before that
// edge. Either way the BFM holds no beat of its own, except that a W channel
// carrying bursts to a cycle-mode BFM is read a burst at a time, when the
// burst's first beat goes on the pins.
template<typename ADDR_T, typename DATA_T, typename STRB_T, typename VL_ADDR_T, typename VL_DATA_T, typename VL_STRB_T,
         typename VL_AWUSER_T = bool, typename VL_WUSER_T = bool, typename VL_BUSER_T = bool, typename VL_ID_T = sc_bv<4>,
         typename AWU = std::monostate, typename WU = std::monostate, typename BU = std::monostate, typename ID = _axiIdT, unsigned IDW = 4>
class axi_write_src_bfm: public sc_module {

public:

    axi_write_out<ADDR_T, DATA_T, STRB_T, AWU, WU, BU, ID, IDW> if_p;
    sc_port<axi_write_hdl_if<VL_ADDR_T, VL_DATA_T, VL_STRB_T, VL_AWUSER_T, VL_WUSER_T, VL_BUSER_T, VL_ID_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi_write_src_bfm);

    axi_write_src_bfm(sc_module_name modulename) : m_lowered(name(), BFM_READY_LOWERED, "clock edges") {
        bfmClocks::add(if_p, clk);
        SC_THREAD(bfm_driver_aw_thread);
        SC_THREAD(bfm_driver_w_thread);
        SC_THREAD(bfm_driver_b_thread);
        SC_METHOD(clock_rise);
        sensitive << clk.pos();
        dont_initialize();
        SC_METHOD(clock_fall);
        sensitive << clk.neg();
        dont_initialize();
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi_write_channel<ADDR_T, DATA_T, STRB_T, AWU, WU, BU, ID, IDW> *>(if_p.get_interface());
        Q_ASSERT_CTX(m_chnl != nullptr, name(), "BFM is bound to an interface that is not an axi_write_channel");
        if_p->setCycleTransaction(PORTTYPE_OUT);
        m_b = dynamic_cast<rdy_vld_channel<axiWriteRespSt<BU, ID, IDW>> *>(m_chnl->m_resp_in.get_interface());
        Q_ASSERT_CTX(m_b != nullptr, name(), "axi_write channel does not carry B on a rdy_vld_channel");
        m_b->setExternalEvent(&m_bOffer);
        m_aw = dynamic_cast<rdy_vld_channel<axiWriteAddressSt<ADDR_T, AWU, ID, IDW>> *>(m_chnl->m_addr_in.get_interface());
        Q_ASSERT_CTX(m_aw != nullptr, name(), "axi_write channel does not carry AW on a rdy_vld_channel");
        m_w = dynamic_cast<rdy_vld_channel<axiWriteDataSt<DATA_T, STRB_T, WU, ID, IDW>> *>(m_chnl->m_data_in.get_interface());
        Q_ASSERT_CTX(m_w != nullptr, name(), "axi_write channel does not carry W on a rdy_vld_channel");
    }

    virtual void end_of_simulation() {
        m_lowered.report();
    }

    void bfm_driver_aw_thread() {
        axiWriteAddressSt<ADDR_T, AWU, ID, IDW> aw_data;
        bool sample = true;
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            if (sample) {
                wait(sc_get_time_resolution());
                hdl_if_p->awready = m_aw->get_rdy();
                if (!m_aw->get_rdy() && m_clock.waitReadyInClock(clk, m_aw->readEnteredEvent(), [this] { return m_aw->get_rdy(); })) {
                    hdl_if_p->awready = true;
                }
            }
            wait(clk.posedge_event());
            if (!rst_n.read()) {
                hdl_if_p->awready = 0;
                while (!rst_n.read()) {
                    wait(clk.posedge_event());
                }
                sample = true;
                continue;
            }
            if (!(hdl_if_p->awvalid && hdl_if_p->awready)) {
                sample = !hdl_if_p->awready;
                continue;
            }
            sample = true;
            aw_data.awid = (ID) hdl_if_p->awid.read().to_uint();
            aw_data.awaddr.sc_unpack(hdl_if_p->awaddr);
            aw_data.awlen = (uint8_t) hdl_if_p->awlen.read().to_uint();
            aw_data.awsize = (_axiSizeT) hdl_if_p->awsize.read().to_uint();
            aw_data.awburst = (_axiBurstT) hdl_if_p->awburst.read().to_uint();
            if constexpr (hasOptionalPayload<AWU>) { aw_data.user.sc_unpack(hdl_if_p->awuser); }
            {
                std::lock_guard<std::mutex> lock(m_pending_mutex);
                m_pending_w_beats = static_cast<int>(aw_data.awlen) + 1;
            }
            // A delayed send blocks across clock edges, and the HDL must not
            // transfer on them.
            hdl_if_p->awready = false;
            if_p->sendAddr(aw_data);
        }
    }

    // wready stays low while sendDataCycle would wait for an address, so the
    // HDL holds a W beat that comes before its AW instead of handing over
    // beats this thread cannot take. An AW can use up the address a waiting
    // burst would take without any W transfer, so wready is driven on every
    // edge.
    bool wReady() {
        return m_chnl->m_data_out->get_rdy() && !m_chnl->sendDataCycleWaitsForAddr();
    }

    void bfm_driver_w_thread() {
        axiWriteDataSt<DATA_T, STRB_T, WU, ID, IDW> w_data;
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            wait(sc_get_time_resolution());
            hdl_if_p->wready = wReady();
            if (!wReady() && m_clock.waitReadyInClock(clk, m_w->readEnteredEvent(), [this] { return wReady(); })) {
                hdl_if_p->wready = true;
            }
            wait(clk.posedge_event());
            if (!rst_n.read()) {
                hdl_if_p->wready = 0;
                // Unblock axi_write_in port_socket waiting on receiveDataCycle.
                int left = 0;
                {
                    std::lock_guard<std::mutex> lock(m_pending_mutex);
                    left = m_pending_w_beats;
                    m_pending_w_beats = 0;
                }
                for (int i = 0; i < left; ++i) {
                    axiWriteDataSt<DATA_T, STRB_T, WU, ID, IDW> dummy{};
                    dummy.wid = 0;
                    dummy.wlast = (i == left - 1);
                    if_p->sendDataCycle(dummy);
                }
                while (!rst_n.read()) {
                    wait(clk.posedge_event());
                }
                continue;
            }
            if (!(hdl_if_p->wvalid && hdl_if_p->wready)) {
                continue;
            }
            w_data.wid = (ID) hdl_if_p->wid.read().to_uint();
            w_data.wdata.sc_unpack(hdl_if_p->wdata);
            w_data.wstrb.sc_unpack(hdl_if_p->wstrb);
            w_data.wlast = (bool) hdl_if_p->wlast.read();
            if constexpr (hasOptionalPayload<WU>) { w_data.user.sc_unpack(hdl_if_p->wuser); }
            {
                std::lock_guard<std::mutex> lock(m_pending_mutex);
                if (m_pending_w_beats > 0) {
                    --m_pending_w_beats;
                }
            }
            hdl_if_p->wready = false;
            if_p->sendDataCycle(w_data);
        }
    }

    // A response the model sends in reset is taken at once and never driven,
    // and one waiting on the pins when reset asserts is dropped.
    void bfm_driver_b_thread() {
        axiWriteRespSt<BU, ID, IDW> b_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->bvalid = 0;
            hdl_if_p->bid = VL_ID_T(0);
            hdl_if_p->bresp = 0;
            if constexpr (hasOptionalPayload<BU>) { hdl_if_p->buser = VL_BUSER_T(0); }
            while (!m_b->offered(b_data)) {
                wait(m_bOffer);
            }
            if (!rst_n.read()) {
                if_p->receiveRespCycle(b_data);
                while (!rst_n.read()) {
                    wait(clk.posedge_event());
                }
                continue;
            }
            m_clock.waitDrivePoint(clk);
            hdl_if_p->bvalid = 1;
            hdl_if_p->bid = b_data.bid;
            hdl_if_p->bresp = b_data.bresp;
            if constexpr (hasOptionalPayload<BU>) { hdl_if_p->buser = b_data.user.sc_pack(); }
            auto taken = [this] { return !rst_n.read() || hdl_if_p->bready.read(); };
            const bool certain = m_clock.waitTaken(clk, taken, [] {});
            if_p->receiveRespCycle(b_data);
            if (certain && !m_clock.waitTakenEdge(clk, rst_n, taken, m_lowered)) {
                do {
                    wait(clk.posedge_event());
                    m_clock.rose();
                } while (!taken());
            }
        }
    }

    void clock_rise() {
        m_clock.rose();
    }

    void clock_fall() {
        m_clock.fell();
    }

private:

    axi_write_channel<ADDR_T, DATA_T, STRB_T, AWU, WU, BU, ID, IDW> * m_chnl = nullptr;
    rdy_vld_channel<axiWriteRespSt<BU, ID, IDW>> * m_b = nullptr;
    rdy_vld_channel<axiWriteAddressSt<ADDR_T, AWU, ID, IDW>> * m_aw = nullptr;
    rdy_vld_channel<axiWriteDataSt<DATA_T, STRB_T, WU, ID, IDW>> * m_w = nullptr;
    sc_event m_bOffer;
    bfmSameClockAnswer m_clock;
    bfmContractCheck m_lowered;
    std::mutex m_pending_mutex;
    int m_pending_w_beats = 0;

};

template<typename ADDR_T, typename DATA_T, typename STRB_T, typename VL_ADDR_T, typename VL_DATA_T, typename VL_STRB_T,
         typename VL_AWUSER_T = bool, typename VL_WUSER_T = bool, typename VL_BUSER_T = bool, typename VL_ID_T = sc_bv<4>,
         typename AWU = std::monostate, typename WU = std::monostate, typename BU = std::monostate, typename ID = _axiIdT, unsigned IDW = 4>
class axi_write_dst_bfm: public sc_module {

public:

    axi_write_in<ADDR_T, DATA_T, STRB_T, AWU, WU, BU, ID, IDW> if_p;
    sc_port<axi_write_hdl_if<VL_ADDR_T, VL_DATA_T, VL_STRB_T, VL_AWUSER_T, VL_WUSER_T, VL_BUSER_T, VL_ID_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi_write_dst_bfm);

    axi_write_dst_bfm(sc_module_name modulename) : m_lowered(name(), BFM_READY_LOWERED, "clock edges") {
        bfmClocks::add(if_p, clk);
        SC_THREAD(bfm_driver_aw_thread);
        SC_THREAD(bfm_driver_w_thread);
        SC_THREAD(bfm_driver_b_thread);
        SC_METHOD(clock_rise);
        sensitive << clk.pos();
        dont_initialize();
        SC_METHOD(clock_fall);
        sensitive << clk.neg();
        dont_initialize();
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi_write_channel<ADDR_T, DATA_T, STRB_T, AWU, WU, BU, ID, IDW> *>(if_p.get_interface());
        Q_ASSERT_CTX(m_chnl != nullptr, name(), "BFM is bound to an interface that is not an axi_write_channel");
        if_p->setCycleTransaction(PORTTYPE_IN);
        m_aw = dynamic_cast<rdy_vld_channel<axiWriteAddressSt<ADDR_T, AWU, ID, IDW>> *>(m_chnl->m_addr_in.get_interface());
        Q_ASSERT_CTX(m_aw != nullptr, name(), "axi_write channel does not carry AW on a rdy_vld_channel");
        m_aw->setExternalEvent(&m_awOffer);
        m_w = dynamic_cast<rdy_vld_channel<axiWriteDataSt<DATA_T, STRB_T, WU, ID, IDW>> *>(m_chnl->m_data_in.get_interface());
        Q_ASSERT_CTX(m_w != nullptr, name(), "axi_write channel does not carry W on a rdy_vld_channel");
        m_w->setExternalEvent(&m_wOffer);
        m_b = dynamic_cast<rdy_vld_channel<axiWriteRespSt<BU, ID, IDW>> *>(m_chnl->m_resp_in.get_interface());
        Q_ASSERT_CTX(m_b != nullptr, name(), "axi_write channel does not carry B on a rdy_vld_channel");
    }

    virtual void end_of_simulation() {
        m_lowered.report();
    }

    void bfm_driver_aw_thread() {
        axiWriteAddressSt<ADDR_T, AWU, ID, IDW> aw_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->awvalid = 0;
            hdl_if_p->awid = VL_ID_T(0);
            hdl_if_p->awaddr = VL_ADDR_T(0);
            hdl_if_p->awlen = 0;
            hdl_if_p->awsize = 0;
            hdl_if_p->awburst = 0;
            if constexpr (hasOptionalPayload<AWU>) { hdl_if_p->awuser = VL_AWUSER_T(0); }
            while (!m_aw->offered(aw_data)) {
                wait(m_awOffer);
            }
            m_clock.waitDrivePoint(clk);
            hdl_if_p->awvalid = 1;
            hdl_if_p->awid = aw_data.awid;
            hdl_if_p->awaddr = aw_data.awaddr.sc_pack();
            hdl_if_p->awlen = aw_data.awlen;
            hdl_if_p->awsize = aw_data.awsize;
            hdl_if_p->awburst = aw_data.awburst;
            if constexpr (hasOptionalPayload<AWU>) { hdl_if_p->awuser = aw_data.user.sc_pack(); }
            auto awready = [this] { return hdl_if_p->awready.read(); };
            const bool certain = m_clock.waitTaken(clk, awready, [] {});
            if_p->receiveAddr(aw_data);
            if (certain && !m_clock.waitTakenEdge(clk, rst_n, awready, m_lowered)) {
                do {
                    wait(clk.posedge_event());
                    m_clock.rose();
                } while (!awready());
            }
        }
    }

    void bfm_driver_w_thread() {
        axiWriteDataSt<DATA_T, STRB_T, WU, ID, IDW> w_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->wvalid = 0;
            hdl_if_p->wid = VL_ID_T(0);
            hdl_if_p->wdata = VL_DATA_T(0);
            hdl_if_p->wstrb = VL_STRB_T(0);
            hdl_if_p->wlast = 0;
            if constexpr (hasOptionalPayload<WU>) { hdl_if_p->wuser = VL_WUSER_T(0); }
            const bool bursts = m_w->isMultiCycle();
            if (bursts) {
                if_p->receiveDataCycle(w_data);
            } else {
                while (!m_w->offered(w_data)) {
                    wait(m_wOffer);
                }
                m_clock.waitDrivePoint(clk);
            }
            hdl_if_p->wvalid = 1;
            hdl_if_p->wid = w_data.wid;
            hdl_if_p->wdata = w_data.wdata.sc_pack();
            hdl_if_p->wstrb = w_data.wstrb.sc_pack();
            hdl_if_p->wlast = w_data.wlast;
            if constexpr (hasOptionalPayload<WU>) { hdl_if_p->wuser = w_data.user.sc_pack(); }
            if (bursts) {
                do {
                    wait(clk.posedge_event());
                    m_clock.rose();
                } while (!hdl_if_p->wready);
                continue;
            }
            auto wready = [this] { return hdl_if_p->wready.read(); };
            const bool certain = m_clock.waitTaken(clk, wready, [] {});
            if_p->receiveDataCycle(w_data);
            if (certain && !m_clock.waitTakenEdge(clk, rst_n, wready, m_lowered)) {
                do {
                    wait(clk.posedge_event());
                    m_clock.rose();
                } while (!wready());
            }
        }
    }

    void bfm_driver_b_thread() {
        axiWriteRespSt<BU, ID, IDW> b_data;
        bool sample = true;
        wait(SC_ZERO_TIME);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            if (sample) {
                wait(sc_get_time_resolution());
                hdl_if_p->bready = m_b->get_rdy();
                if (!m_b->get_rdy() && m_clock.waitReadyInClock(clk, m_b->readEnteredEvent(), [this] { return m_b->get_rdy(); })) {
                    hdl_if_p->bready = true;
                }
            }
            wait(clk.posedge_event());
            if (!(hdl_if_p->bvalid && hdl_if_p->bready)) {
                sample = !hdl_if_p->bready;
                continue;
            }
            sample = true;
            b_data.bid = (ID) hdl_if_p->bid.read().to_uint();
            b_data.bresp = (_axiResponseT) hdl_if_p->bresp.read().to_uint();
            if constexpr (hasOptionalPayload<BU>) { b_data.user.sc_unpack(hdl_if_p->buser); }
            hdl_if_p->bready = false;
            if_p->sendRespCycle(b_data);
        }
    }

    void clock_rise() {
        m_clock.rose();
    }

    void clock_fall() {
        m_clock.fell();
    }

private:

    axi_write_channel<ADDR_T, DATA_T, STRB_T, AWU, WU, BU, ID, IDW> * m_chnl = nullptr;
    rdy_vld_channel<axiWriteAddressSt<ADDR_T, AWU, ID, IDW>> * m_aw = nullptr;
    rdy_vld_channel<axiWriteDataSt<DATA_T, STRB_T, WU, ID, IDW>> * m_w = nullptr;
    rdy_vld_channel<axiWriteRespSt<BU, ID, IDW>> * m_b = nullptr;
    sc_event m_awOffer;
    sc_event m_wOffer;
    bfmSameClockAnswer m_clock;
    bfmContractCheck m_lowered;

};

#endif /* AXI_WRITE_BFM_H_ */
