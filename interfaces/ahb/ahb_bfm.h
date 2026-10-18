#ifndef AHB_BFM_H_
#define AHB_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "ahb_channel.h"

#include <algorithm>
#include <deque>
#include <optional>

template<typename VL_ADDR_T, typename VL_DATA_T>
struct ahb_hdl_if: public sc_interface {
    sc_signal<VL_ADDR_T> haddr;
    sc_signal<bool> hsel;
    sc_signal<sc_bv<AHB_TRANS_WIDTH>> htrans;
    sc_signal<bool> hwrite;
    sc_signal<sc_bv<AHB_SIZE_WIDTH>> hsize;
    sc_signal<sc_bv<AHB_BURST_WIDTH>> hburst;
    sc_signal<sc_bv<AHB_PROT_WIDTH>> hprot;
    sc_signal<bool> hmastlock;
    sc_signal<VL_DATA_T> hwdata;
    sc_signal<bool> hready;
    sc_signal<VL_DATA_T> hrdata;
    sc_signal<bool> hresp;
};

// Bridge for an RTL manager. The BFM is the subordinate on the pins and the
// manager on the model channel. It samples a transfer at a clock edge where
// hready is high, hsel is high and htrans is NONSEQ or SEQ, and holds hready low
// until the model responds. IDLE and BUSY get a zero-wait OKAY.
template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class ahb_src_bfm: public sc_module {

public:

    ahb_out<ADDR_T, DATA_T> if_p;
    sc_port<ahb_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (ahb_src_bfm);

    ahb_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        hdl_if_p->hready = true;
        hdl_if_p->hresp = false;
        hdl_if_p->hrdata = VL_DATA_T(0);
        do { wait(clk.posedge_event()); } while (!rst_n);
        // The edge that releases reset can already end an address phase, so
        // each pass samples the edge it starts on.
        while (true) {
            hdl_if_p->hresp = false;
            hdl_if_p->hrdata = VL_DATA_T(0);
            const _ahbTransT htrans = (_ahbTransT) hdl_if_p->htrans.read().to_uint();
            if (hdl_if_p->hsel && (htrans == AHBTRANS_NONSEQ || htrans == AHBTRANS_SEQ)) {
                ahbAddrSt<ADDR_T> addr;
                addr.haddr.sc_unpack(hdl_if_p->haddr);
                addr.htrans = htrans;
                addr.hwrite = hdl_if_p->hwrite;
                addr.hsize = (_ahbSizeT) hdl_if_p->hsize.read().to_uint();
                addr.hburst = (_ahbBurstT) hdl_if_p->hburst.read().to_uint();
                addr.hprot = (_ahbProtT) hdl_if_p->hprot.read().to_uint();
                addr.hmastlock = hdl_if_p->hmastlock;
                // Wait states until the model responds.
                hdl_if_p->hready = false;
                if_p->sendAddr(addr);
                if (addr.hwrite) {
                    // The manager drives hwdata from the start of the data phase and
                    // holds it while hready is low, so any falling edge from here on
                    // sees it.
                    wait(clk.negedge_event());
                    DATA_T data;
                    data.sc_unpack(hdl_if_p->hwdata);
                    if_p->sendData(data);
                }
                ahbRespSt<DATA_T> resp;
                if_p->receiveResp(resp);
                if (!addr.hwrite) {
                    hdl_if_p->hrdata = VL_DATA_T(resp.hrdata.sc_pack());
                }
                if (resp.hresp) {
                    // ERROR takes two cycles, the first with hready low.
                    hdl_if_p->hresp = true;
                    wait(clk.posedge_event());
                }
                hdl_if_p->hready = true;
            }
            // hready is high in the cycle this edge ends, so the edge ends the
            // previous data phase and any address phase on the bus.
            wait(clk.posedge_event());
        }
    }

};

// Bridge for an RTL subordinate. The BFM is the manager on the pins and the
// subordinate on the model channel. It drives the address phase of the next
// transfer during the data phase of the current one, holds the address phase
// and hwdata while hready is low, and carries on after an ERROR response.
// When the model has no transfer ready it drives BUSY inside a burst that has
// beats left or is an open INCR, with the burst's control and the next beat's
// address, and IDLE with hsel low otherwise. hmastlock keeps the value of the
// last transfer, so a locked sequence stays locked across those cycles.
template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class ahb_dst_bfm: public sc_module {

public:

    ahb_in<ADDR_T, DATA_T> if_p;
    sc_port<ahb_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (ahb_dst_bfm);

    ahb_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_fetch_thread);
        SC_THREAD(bfm_driver_thread);
        SC_THREAD(bfm_resp_thread);
    }

private:

    struct transfer {
        ahbAddrSt<ADDR_T> addr;
        DATA_T wdata;
    };

    // The write data must be in hand before the address phase starts, because
    // the manager cannot stall its own data phase. The fetch thread takes one
    // transfer ahead of the bus.
    std::deque<transfer> m_issue;
    sc_event m_issue_taken;
    // Responses wait here for the model, so a slow receiveResp() never holds
    // up the bus.
    std::deque<ahbRespSt<DATA_T>> m_resp;
    sc_event m_resp_added;

    // The burst of the last transfer driven.
    ahbAddrSt<ADDR_T> m_burst;   // its control signals
    int m_beats_left = 0;        // beats still to come, -1 for INCR
    VL_ADDR_T m_next_addr;       // address of its next beat

    void bfm_fetch_thread() {
        while (true) {
            while (!m_issue.empty()) {
                wait(m_issue_taken);
            }
            transfer t;
            if_p->receiveAddr(t.addr);
            if (t.addr.hwrite) {
                if_p->receiveData(t.wdata);
            }
            m_issue.push_back(t);
        }
    }

    static bool isWrap(_ahbBurstT burst) {
        return burst == AHBBURST_WRAP4 || burst == AHBBURST_WRAP8 || burst == AHBBURST_WRAP16;
    }

    // Address of the beat after addr, within addr's 1KB block. An incrementing
    // burst that reaches the end of the block wraps to its start here, and
    // startBeat ends that burst instead.
    static VL_ADDR_T beatAfter(VL_ADDR_T addr, _ahbSizeT size, _ahbBurstT burst) {
        const int bits = std::min(addr.length(), 10);
        const uint64_t bytes = uint64_t(1) << size;
        const uint64_t low = addr.range(bits - 1, 0).to_uint64();
        uint64_t next = low + bytes;
        if (isWrap(burst)) {
            const uint64_t span = bytes * (burst == AHBBURST_WRAP4 ? 4 : burst == AHBBURST_WRAP8 ? 8 : 16);
            next = (low & ~(span - 1)) | (next & (span - 1));
        }
        addr.range(bits - 1, 0) = next;
        return addr;
    }

    void startBeat(const ahbAddrSt<ADDR_T> &addr) {
        if (addr.htrans == AHBTRANS_NONSEQ) {
            switch (addr.hburst) {
                case AHBBURST_SINGLE: m_beats_left = 0; break;
                case AHBBURST_INCR: m_beats_left = -1; break;
                case AHBBURST_WRAP4: case AHBBURST_INCR4: m_beats_left = 3; break;
                case AHBBURST_WRAP8: case AHBBURST_INCR8: m_beats_left = 7; break;
                case AHBBURST_WRAP16: case AHBBURST_INCR16: m_beats_left = 15; break;
            }
        } else {
            Q_ASSERT(m_beats_left != 0, "ahb SEQ with no burst in progress");
            if (m_beats_left > 0) {
                m_beats_left--;
            }
        }
        m_burst = addr;
        m_next_addr = beatAfter(addr.haddr.sc_pack(), addr.hsize, addr.hburst);
        // A burst never crosses a 1KB boundary, so an incrementing burst whose
        // next beat would start a new 1KB block has no next beat.
        const int bits = std::min(m_next_addr.length(), 10);
        if (!isWrap(addr.hburst) && m_next_addr.range(bits - 1, 0).to_uint64() == 0) {
            m_beats_left = 0;
        }
    }

    void driveAddr(const std::optional<transfer> &ap, bool busy) {
        if (ap) {
            hdl_if_p->hsel = true;
            hdl_if_p->haddr = ap->addr.haddr.sc_pack();
            hdl_if_p->htrans = ap->addr.htrans;
            hdl_if_p->hwrite = ap->addr.hwrite;
            hdl_if_p->hsize = ap->addr.hsize;
            hdl_if_p->hburst = ap->addr.hburst;
            hdl_if_p->hprot = ap->addr.hprot;
            hdl_if_p->hmastlock = ap->addr.hmastlock;
        } else if (busy) {
            hdl_if_p->hsel = true;
            hdl_if_p->haddr = m_next_addr;
            hdl_if_p->htrans = AHBTRANS_BUSY;
            hdl_if_p->hwrite = m_burst.hwrite;
            hdl_if_p->hsize = m_burst.hsize;
            hdl_if_p->hburst = m_burst.hburst;
            hdl_if_p->hprot = m_burst.hprot;
            hdl_if_p->hmastlock = m_burst.hmastlock;
        } else {
            hdl_if_p->hsel = false;
            hdl_if_p->haddr = VL_ADDR_T(0);
            hdl_if_p->htrans = AHBTRANS_IDLE;
            hdl_if_p->hwrite = false;
            hdl_if_p->hsize = 0;
            hdl_if_p->hburst = 0;
            hdl_if_p->hprot = 0;
            hdl_if_p->hmastlock = m_burst.hmastlock;
        }
    }

    void bfm_driver_thread() {
        std::optional<transfer> ap; // in its address phase
        bool busy = false;          // BUSY in the address phase
        std::optional<transfer> dp; // in its data phase
        m_burst.hmastlock = false;
        driveAddr(ap, busy);
        hdl_if_p->hwdata = VL_DATA_T(0);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            driveAddr(ap, busy);
            if (dp && dp->addr.hwrite) {
                hdl_if_p->hwdata = dp->wdata.sc_pack();
            } else {
                hdl_if_p->hwdata = VL_DATA_T(0);
            }
            wait(clk.posedge_event());
            if (!hdl_if_p->hready) {
                // Wait state, or the first cycle of an ERROR response.
                continue;
            }
            if (dp) {
                ahbRespSt<DATA_T> resp;
                resp.hresp = hdl_if_p->hresp;
                if (!dp->addr.hwrite) {
                    resp.hrdata.sc_unpack(hdl_if_p->hrdata);
                }
                m_resp.push_back(resp);
                m_resp_added.notify(SC_ZERO_TIME);
            }
            dp = ap;
            ap.reset();
            if (!m_issue.empty()) {
                ap = m_issue.front();
                m_issue.pop_front();
                m_issue_taken.notify(SC_ZERO_TIME);
                startBeat(ap->addr);
            }
            busy = !ap && m_beats_left != 0;
        }
    }

    void bfm_resp_thread() {
        while (true) {
            while (m_resp.empty()) {
                wait(m_resp_added);
            }
            ahbRespSt<DATA_T> resp = m_resp.front();
            m_resp.pop_front();
            if_p->sendResp(resp);
        }
    }

};

#endif /* AHB_BFM_H_ */
