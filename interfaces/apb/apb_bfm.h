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

    // A write is posted: request() returns before the model's reqReceive()
    // takes it. PREADY waits until the model has, so the BFM holds no write
    // of its own.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            ADDR_T addr;
            DATA_T data;
            bool is_write;
            hdl_if_p->pslverr = false;
            hdl_if_p->pready = false;
            hdl_if_p->prdata = VL_DATA_T(0);
            while ( !(hdl_if_p->psel && hdl_if_p->penable )) {
                wait(clk.posedge_event());
            }
            is_write = hdl_if_p->pwrite;
            addr.sc_unpack(hdl_if_p->paddr);
            if( is_write ) {
                data.sc_unpack(hdl_if_p->pwdata);
            }
            m_held.take(pins());
            m_held.inCall_ = true;
            if_p->request(is_write, addr, data);
            m_held.inCall_ = false;
            do {
                waitEdge();
            } while (is_write && m_chnl->isActive());
            hdl_if_p->pready = true;
            if( !is_write ) {
                hdl_if_p->prdata = VL_DATA_T(data.sc_pack());
            }
            waitEdge();
            hdl_if_p->pslverr = false;
            hdl_if_p->pready = false;
            hdl_if_p->prdata = VL_DATA_T(0);
            while ( hdl_if_p->psel && hdl_if_p->penable ) {
              wait(clk.posedge_event());
            };
        }
    }

    void request_monitor() {
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
    bool selected() const { return hdl_if_p->psel && hdl_if_p->penable; }
    void waitEdge() {
        wait(clk.posedge_event());
        if (rst_n) {
            m_held.check(selected(), pins());
        }
    }

    apb_channel<ADDR_T, DATA_T> *m_chnl = nullptr;
    bfmHeldRequest<pinsT> m_held;

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

    apb_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<apb_channel<ADDR_T, DATA_T> *>(if_p.get_interface());
        Q_ASSERT_CTX(m_chnl != nullptr, name(), "BFM is bound to an interface that is not an apb_channel");
        if_p->setExternalEvent(&m_offer);
    }

    // A request stays the model's until the HDL completes it. The BFM shows
    // the offered request on the pins and takes it with reqReceive() on the
    // edge PREADY completes it, so a posted write holds the model's next
    // request() as the RTL's single APB transfer would, and the BFM holds no
    // write of its own.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            ADDR_T addr;
            DATA_T data;
            bool is_write;
            bool slverr;
            while (!m_chnl->offered(is_write, addr, data)) {
                wait(m_offer);
            }
            hdl_if_p->psel = true;
            hdl_if_p->paddr = addr.sc_pack();
            if ( is_write ) {
                hdl_if_p->pwrite = true;
                hdl_if_p->pwdata = data.sc_pack();
            }
            wait(clk.posedge_event());
            hdl_if_p->penable = true;
            // Count access-phase cycles where the slave holds PREADY low (wait states).
            uint32_t wait_cycles = 0;
            for (;;) {
                wait(clk.posedge_event());
                if (hdl_if_p->pready) {
                    break;
                }
                if (wait_cycles < 255u) {
                    ++wait_cycles;
                }
            }
            if ( !is_write ) {
                data.sc_unpack(hdl_if_p->prdata);
            }
            slverr = hdl_if_p->pslverr;
            // The channel's timed delay runs in reqReceive() and complete(),
            // after the pins are released, so the slave never sees a select
            // without an access.
            hdl_if_p->penable = false;
            hdl_if_p->psel = false;
            hdl_if_p->paddr = VL_ADDR_T(0);
            hdl_if_p->pwrite = false;
            hdl_if_p->pwdata = VL_DATA_T(0);
            {
                ADDR_T takenAddr;
                DATA_T takenData;
                bool takenWrite;
                if_p->reqReceive(takenWrite, takenAddr, takenData);
            }
            if( !is_write ) if_p->complete(data);

            if (!observe_ifc.empty()) {
                const uint32_t addr_u = static_cast<uint32_t>(addr._getAddress());
                const uint32_t data_u = static_cast<uint32_t>(data._getData());
                socket_observe_apb_resp(observe_ifc, is_write, addr_u, data_u,
                                        static_cast<uint8_t>(wait_cycles), true);
            }

            // PSLVERR is legal for unmapped APB (rev3 §11.5); do not fatal.
            (void)slverr;
        }
    }

private:

    apb_channel<ADDR_T, DATA_T> *m_chnl = nullptr;
    sc_event m_offer;

};

#endif /* APB_BFM_H_ */
