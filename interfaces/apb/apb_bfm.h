#ifndef APB_BFM_H_
#define APB_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "apb_channel.h"
#include "socketObserve.h"
#include "bfmContractCheck.h"

#include <cstdint>
#include <string>
#include <tuple>

template<typename VL_ADDR_T, typename VL_DATA_T>
struct apb_hdl_if: public sc_interface {
    sc_signal<VL_ADDR_T> paddr;
    sc_signal<bool> psel;
    sc_signal<bool> penable;
    sc_signal<bool> pwrite;
    sc_signal<VL_DATA_T> pwdata;
    sc_signal<bool> pready;
    sc_signal<VL_DATA_T> prdata;
    sc_signal<bool> pslverr;
};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class apb_src_bfm: public sc_module {

public:

    apb_out<ADDR_T, DATA_T> if_p;
    sc_port<apb_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (apb_src_bfm);

    apb_src_bfm(sc_module_name modulename) : m_held(name()) {
        bfmClocks::add(if_p, clk);
        SC_THREAD(bfm_driver_thread);
        SC_METHOD(request_monitor);
        sensitive << clk.pos();
        dont_initialize();
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<apb_channel<ADDR_T, DATA_T> *>(if_p.get_interface());
        Q_ASSERT_CTX(m_chnl != nullptr, name(), "BFM is bound to an interface that is not an apb_channel");
    }

    virtual void end_of_simulation() {
        m_held.check_.report();
    }

    // The BFM takes each transfer at the edge that samples its setup phase,
    // when APB has fixed the address, direction and write data, so a model
    // that answers in zero time completes it in the first access phase, as a
    // slave with no wait states does. A write is posted, so PREADY waits
    // until the model's reqReceive() has taken it and the BFM holds no write
    // of its own.
    void bfm_driver_thread() {
        hdl_if_p->pslverr = false;
        hdl_if_p->pready = false;
        hdl_if_p->prdata = VL_DATA_T(0);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            if (!hdl_if_p->psel) {
                wait(clk.posedge_event());
                continue;
            }
            ADDR_T addr;
            DATA_T data;
            const bool is_write = hdl_if_p->pwrite;
            addr.sc_unpack(hdl_if_p->paddr);
            if( is_write ) {
                data.sc_unpack(hdl_if_p->pwdata);
            }
            m_edge = sc_time_stamp();
            m_held.take(pins());
            m_held.inCall_ = true;
            if_p->request(is_write, addr, data);
            m_held.inCall_ = false;
            waitDrivePoint(is_write);
            hdl_if_p->pready = true;
            if( !is_write ) {
                hdl_if_p->prdata = VL_DATA_T(data.sc_pack());
            }
            waitEdge();
            hdl_if_p->pslverr = false;
            hdl_if_p->pready = false;
            hdl_if_p->prdata = VL_DATA_T(0);
            wait(clk.posedge_event());
        }
    }

    void request_monitor() {
        m_edge = sc_time_stamp();
        if (rst_n) {
            m_held.monitor(selected(), pins());
        }
    }

private:

    // PWDATA carries nothing on a read, so a read compares it as zero.
    using pinsT = std::tuple<VL_ADDR_T, bool, VL_DATA_T>;
    pinsT pins() const {
        const bool is_write = hdl_if_p->pwrite;
        return {hdl_if_p->paddr.read(), is_write, is_write ? hdl_if_p->pwdata.read() : VL_DATA_T(0)};
    }
    // APB holds PSEL from the setup phase to the edge that completes the
    // transfer.
    bool selected() const { return hdl_if_p->psel; }
    void waitEdge() {
        wait(clk.posedge_event());
        m_edge = sc_time_stamp();
        if (rst_n) {
            m_held.check(selected(), pins());
        }
    }
    // Returns at the first drive point, one time resolution step after an
    // edge, by which the model has answered: a read's request() has
    // returned, and the model has taken a write. A model that answers later
    // than the drive point, between edges, is answered at the next edge's.
    void waitDrivePoint(bool is_write) {
        const sc_time step = sc_get_time_resolution();
        while (true) {
            const sc_time point = m_edge + step;
            if (sc_time_stamp() <= point) {
                if (sc_time_stamp() < point) {
                    wait(point - sc_time_stamp());
                }
                if (!(is_write && m_chnl->isActive())) {
                    return;
                }
            }
            waitEdge();
        }
    }

    apb_channel<ADDR_T, DATA_T> *m_chnl = nullptr;
    bfmHeldRequest<pinsT> m_held;
    // The last rising edge, seen by the driver or, while the driver is in
    // the model's call, by request_monitor().
    sc_time m_edge;

};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class apb_dst_bfm: public sc_module {

public:

    apb_in<ADDR_T, DATA_T> if_p;
    sc_port<apb_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    // When set (e.g. "cpu_apb_reg"), emit pin-accurate RESP observe with wait_cycles.
    std::string observe_ifc;

    SC_HAS_PROCESS (apb_dst_bfm);

    apb_dst_bfm(sc_module_name modulename) :
        m_lowered(name()),
        m_prdataChanged(name()),
        m_complete([this] { complete(); }) {
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
        m_chnl = dynamic_cast<apb_channel<ADDR_T, DATA_T> *>(if_p.get_interface());
        Q_ASSERT_CTX(m_chnl != nullptr, name(), "BFM is bound to an interface that is not an apb_channel");
        if_p->setExternalEvent(&m_offer);
    }

    virtual void end_of_simulation() {
        m_lowered.report();
        m_prdataChanged.report();
    }

    // A request stays the model's until the HDL completes it. The BFM shows
    // the offered request on the pins and takes it with reqReceive() at the
    // sample point of the access phase whose closing edge PREADY completes
    // (bfmSameClockAnswer::waitTaken()), so a posted write holds the model's
    // next request() as the RTL's single APB transfer would, and the BFM
    // holds no write of its own.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        m_clock.rose();
        auto ready = [this] { return hdl_if_p->pready.read(); };
        while (true) {
            while (!m_chnl->offered(m_isWrite, m_addr, m_data)) {
                wait(m_offer);
            }
            m_clock.waitDrivePoint(clk);
            hdl_if_p->psel = true;
            hdl_if_p->paddr = m_addr.sc_pack();
            if ( m_isWrite ) {
                hdl_if_p->pwrite = true;
                hdl_if_p->pwdata = m_data.sc_pack();
            }
            wait(clk.posedge_event());
            m_clock.rose();
            hdl_if_p->penable = true;
            // Count access-phase cycles where the slave holds PREADY low (wait states).
            uint32_t wait_cycles = 0;
            const bool certain = m_clock.waitTaken(clk, ready, [this, &wait_cycles] {
                if (!hdl_if_p->pready && wait_cycles < 255u) {
                    ++wait_cycles;
                }
            });
            if ( !m_isWrite ) {
                m_data.sc_unpack(hdl_if_p->prdata);
                m_prdataChanged.sample(hdl_if_p->prdata.read());
            }
            m_complete.start();
            if (certain) {
                if (m_clock.waitTakenEdge(clk, rst_n, ready, m_lowered)) {
                    if (!m_isWrite && rst_n.read()) {
                        m_prdataChanged.check(&m_clock, hdl_if_p->prdata.read());
                    }
                } else {
                    do {
                        wait(clk.posedge_event());
                        m_clock.rose();
                    } while (!ready());
                }
            }
            hdl_if_p->penable = false;
            hdl_if_p->psel = false;
            hdl_if_p->paddr = VL_ADDR_T(0);
            hdl_if_p->pwrite = false;
            hdl_if_p->pwdata = VL_DATA_T(0);
            m_complete.waitDone();

            if (!observe_ifc.empty()) {
                const uint32_t addr_u = static_cast<uint32_t>(m_addr._getAddress());
                const uint32_t data_u = static_cast<uint32_t>(m_data._getData());
                socket_observe_apb_resp(observe_ifc, m_isWrite, addr_u, data_u,
                                        static_cast<uint8_t>(wait_cycles), true);
            }
        }
    }

    void edge_monitor() {
        m_clock.rose();
    }

    void clock_fall() {
        m_clock.fell();
    }

private:

    // The channel's timed delay runs in reqReceive() and complete(), on the
    // completer's thread, so the slave never sees a select without an access.
    void complete() {
        ADDR_T takenAddr;
        DATA_T takenData;
        bool takenWrite;
        if_p->reqReceive(takenWrite, takenAddr, takenData);
        if ( !m_isWrite ) {
            if_p->complete(m_data);
        }
    }

    apb_channel<ADDR_T, DATA_T> *m_chnl = nullptr;
    sc_event m_offer;
    ADDR_T m_addr;
    DATA_T m_data;
    bool m_isWrite = false;
    bfmSameClockAnswer m_clock;
    bfmReadyLowered m_lowered;
    bfmReadDataChanged<VL_DATA_T> m_prdataChanged;
    bfmCompleter m_complete;

};

#endif /* APB_BFM_H_ */
