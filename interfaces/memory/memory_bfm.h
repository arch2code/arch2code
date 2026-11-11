#ifndef MEMORY_BFM_H_
#define MEMORY_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "memory_channel.h"
#include "bfmContractCheck.h"
#include "q_assert.h"
#include <cstdint>
#include <format>
#include <list>
#include <string>

template<typename VL_ADDR_T, typename VL_DATA_T>
struct memory_hdl_if: public sc_interface {
    sc_signal<VL_ADDR_T> addr;
    sc_signal<bool> enable;
    sc_signal<bool> wr_en;
    sc_signal<VL_DATA_T> write_data;
    sc_signal<VL_DATA_T> read_data;
};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class memory_src_bfm: public sc_module {

public:

    memory_out<ADDR_T, DATA_T> if_p;
    sc_port<memory_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (memory_src_bfm);

    memory_src_bfm(sc_module_name modulename) :
        m_skipped(name(), "HDL made a memory access while SystemC was still serving the previous one, so the BFM did not take it",
                  "accesses") {
        SC_THREAD(bfm_driver_thread);
        SC_METHOD(edge_monitor);
        sensitive << clk.pos();
        dont_initialize();
    }

    virtual void end_of_simulation() {
        m_skipped.report();
    }

    // One access per rising edge with enable high, as on memory_sp/memory_dp. Read
    // data is driven on the edge that samples the access and holds until the next
    // read. The Verilated model is an SC_METHOD woken by the same edge, so the RTL
    // evaluates that edge with the old read_data and sees the new value after it,
    // like a flop output.
    // request() must not consume simulated time. An enabled edge that passes while
    // it waits, such as a tandem memory tee waiting for the model side, is never
    // served, and m_skipped counts it.
    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        hdl_if_p->read_data = VL_DATA_T(0);
        while (true) {
            if (hdl_if_p->enable) {
                ADDR_T addr;
                DATA_T data;
                bool is_write = hdl_if_p->wr_en;
                addr.sc_unpack(hdl_if_p->addr);
                if (is_write) {
                    data.sc_unpack(hdl_if_p->write_data);
                }
                m_sampleTime = sc_time_stamp();
                m_requesting = true;
                if_p->request(is_write, addr, data);
                m_requesting = false;
                if (!is_write) {
                    hdl_if_p->read_data = VL_DATA_T(data.sc_pack());
                }
                // The next wait cannot see an edge in this delta. edge_monitor has
                // counted that edge only if it ran first.
                if (clk.posedge() && sc_time_stamp() > m_sampleTime && hdl_if_p->enable &&
                    m_lastSkip != sc_time_stamp()) {
                    skipped();
                }
            }
            wait(clk.posedge_event());
        }
    }

    void edge_monitor() {
        if (m_requesting && sc_time_stamp() > m_sampleTime && hdl_if_p->enable) {
            skipped();
        }
    }

private:

    void skipped() {
        m_lastSkip = sc_time_stamp();
        m_skipped.fail(m_lastSkip);
    }

    bool m_requesting = false;
    sc_time m_sampleTime;
    sc_time m_lastSkip;
    bfmContractCheck m_skipped;

};

// Shared by the memory_dst_bfms of one UVM SystemC wrapper whose run holds
// the model alone. A model's write is posted, so its later access through
// another port can reach the pins with or before the write, and a memory that
// serves both at one edge reads first. Each channel stamps an access as the
// requester's request() starts, in that thread; an adapter that relays the
// request passes the stamp through (observeRelayed()), so the stamp is taken
// in the original caller's thread. A BFM holds an access until the earlier
// accesses on the other ports allow it: a read is sampled after every earlier
// write; a write is sampled after every earlier write and no earlier than
// every earlier read, which on the same clock means on the read's edge or
// later, and on another clock after it. A hold waits only for earlier
// accesses. Two model threads that issue in one evaluation phase race: the
// stamps follow the order the kernel runs them.
class memory_write_order {
public:
    struct access {
        uint64_t seq;
        const sc_module *bfm;
        const sc_interface *clock;
        bool isWrite;
        bool taken;
        bool onPins;
    };
    using entry = std::list<access>::iterator;

    void issue(const sc_module *bfm, const sc_interface *clock, bool isWrite) {
        m_pending.push_back({m_next++, bfm, clock, isWrite, false, false});
    }
    // The access bfm takes next, its oldest one not yet taken; false if its
    // channel never stamped one.
    bool take(const sc_module *bfm, entry &a) {
        for (a = m_pending.begin(); a != m_pending.end(); ++a) {
            if (a->bfm == bfm && !a->taken) {
                a->taken = true;
                return true;
            }
        }
        return false;
    }
    // The earliest access on another port that holds a, or nullptr.
    const access *blocker(entry a) const {
        for (const access &x : m_pending) {
            if (x.seq >= a->seq) break;
            if (x.bfm == a->bfm) continue;
            if (x.isWrite) return &x;
            if (a->isWrite && !(x.onPins && x.clock == a->clock)) return &x;
        }
        return nullptr;
    }
    void onPins(entry a) {
        a->onPins = true;
        m_changed.notify();
    }
    void sampled(entry a) {
        m_pending.erase(a);
        m_changed.notify();
    }
    const sc_event &changed() const { return m_changed; }

private:
    std::list<access> m_pending;
    uint64_t m_next = 0;
    sc_event m_changed;
};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class memory_dst_bfm: public sc_module {

public:

    memory_in<ADDR_T, DATA_T> if_p;
    sc_port<memory_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (memory_dst_bfm);

    memory_dst_bfm(sc_module_name modulename) : log_(name()) {
        SC_THREAD(bfm_driver_thread);
    }

    // UVM Mode B only. credit counts the accesses the DUT lane has made on
    // this port, and the model's access n reaches the pins only once credit
    // exceeds n, so the model lane never runs ahead of the RTL's access and
    // replays the word the RTL read. held is high while an access waits.
    void setModelCredit(sc_signal<sc_bv<32>> *credit, sc_signal<bool> *held) {
        m_credit = credit;
        m_held = held;
    }

    // During elaboration only: the channel stamps each request from the
    // start of the simulation.
    void setWriteOrder(memory_write_order *order) {
        Q_ASSERT(sc_get_status() < SC_END_OF_ELABORATION, "setWriteOrder() called after elaboration");
        m_order = order;
    }

    void end_of_elaboration() override {
        // The credit replays the RTL's words, which the order would only delay.
        Q_ASSERT(m_order == nullptr || m_credit == nullptr, "a memory_dst_bfm has both a write order and a model credit");
        if (m_order != nullptr) {
            const sc_interface *clock = clk.get_interface();
            if_p->setRequestObserver([this, clock](bool isWrite) { m_order->issue(this, clock, isWrite); });
        }
    }

    virtual void end_of_simulation() {
        if (m_waiting) {
            const uint32_t credit = m_credit->read().to_uint();
            // Credit past the access means the BFM missed the change that
            // released it, not that the DUT lane stopped.
            const std::string cause = static_cast<int32_t>(credit - m_issued) > 0
                ? std::string("the credit had released it, so the BFM missed its wake-up")
                : std::format("the DUT lane never made access {}", m_issued + 1);
            log_.logPrint(std::format("the model's access {} ({} {}) waited for credit from {} to the end, with {} issued and credit {}: {}",
                                      m_issued + 1, m_heldWrite ? "write" : "read", m_heldAddr.prt(false),
                                      m_heldSince.to_string(), m_issued, credit, cause),
                          LOG_IMPORTANT);
        }
        if (m_orderWaiting) {
            log_.logPrint(std::format("the model's access {} ({} {}) waited for the write order from {} to the end, behind the earlier {} on {}",
                                      m_taken, m_orderWrite ? "write" : "read", m_orderAddr.prt(false),
                                      m_orderSince.to_string(), m_orderBlockerWrite ? "write" : "read",
                                      m_orderBlocker->name()),
                          LOG_IMPORTANT);
        }
    }

    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            ADDR_T addr;
            DATA_T data;
            bool is_write;
            if_p->reqReceive(is_write, addr, data);
            m_taken++;
            if (m_credit != nullptr) {
                waitCredit(is_write, addr);
            }
            memory_write_order::entry stamp;
            if (m_order != nullptr) {
                if (!m_order->take(this, stamp)) {
                    Q_ASSERT(false, "memory_write_order: the BFM took an access its channel never stamped");
                    return;
                }
                waitOrder(stamp, is_write, addr);
            }
            hdl_if_p->enable = true;
            hdl_if_p->addr = addr.sc_pack();
            if (is_write) {
                hdl_if_p->wr_en = true;
                hdl_if_p->write_data = data.sc_pack();
            } else {
                hdl_if_p->wr_en = false;
            }
            wait(clk.posedge_event());
            if (m_order != nullptr) {
                m_order->sampled(stamp);
            }
            hdl_if_p->enable = false;
            hdl_if_p->addr = VL_ADDR_T(0);
            hdl_if_p->wr_en = false;
            hdl_if_p->write_data = VL_DATA_T(0);
            if (!is_write) {
                // read_data changes after the access edge: deltas later from RTL,
                // one drive skew later from a UVM agent. It is stable by the
                // falling edge, before the next access edge.
                wait(clk.negedge_event());
                data.sc_unpack(hdl_if_p->read_data);
                // The model resumes at the next rising edge, so the pins it
                // drives next change after a posedge, never at the falling edge
                // where UVM monitors sample. A read takes two edges.
                wait(clk.posedge_event());
                if_p->complete(data);
            }
        }
    }

private:

    // The credit pin changes at the UVM drive point, 100 ps after a rising
    // edge, so an access released here stays on the pins through the next
    // rising edge. The difference wraps with the 32-bit count.
    void waitCredit(bool is_write, const ADDR_T &addr) {
        while (static_cast<int32_t>(m_credit->read().to_uint() - m_issued) <= 0) {
            if (!m_waiting) {
                m_waiting = true;
                m_heldWrite = is_write;
                m_heldAddr = addr;
                m_heldSince = sc_time_stamp();
                m_held->write(true);
            }
            wait(m_credit->value_changed_event());
        }
        if (m_waiting) {
            m_waiting = false;
            m_held->write(false);
        }
        m_issued++;
    }

    void waitOrder(memory_write_order::entry stamp, bool is_write, const ADDR_T &addr) {
        while (const memory_write_order::access *blocker = m_order->blocker(stamp)) {
            if (!m_orderWaiting) {
                m_orderWaiting = true;
                m_orderWrite = is_write;
                m_orderAddr = addr;
                m_orderSince = sc_time_stamp();
            }
            m_orderBlocker = blocker->bfm;
            m_orderBlockerWrite = blocker->isWrite;
            m_orderBlockerClock = blocker->clock;
            wait(m_order->changed());
        }
        // A blocker on another clock releases at that clock's edge, which
        // can fall in this clock's low phase, where pins driven now would
        // drop at the next rising edge before a UVM agent samples them at
        // the falling edge.
        if (m_orderWaiting && m_orderBlockerClock != clk.get_interface()) {
            wait(clk.posedge_event());
        }
        m_orderWaiting = false;
        m_order->onPins(stamp);
    }

    logBlock log_;
    sc_signal<sc_bv<32>> *m_credit = nullptr;
    sc_signal<bool> *m_held = nullptr;
    memory_write_order *m_order = nullptr;
    uint32_t m_issued = 0;
    bool m_waiting = false;
    bool m_heldWrite = false;
    ADDR_T m_heldAddr;
    sc_time m_heldSince;
    uint64_t m_taken = 0;
    bool m_orderWaiting = false;
    bool m_orderWrite = false;
    ADDR_T m_orderAddr;
    sc_time m_orderSince;
    const sc_module *m_orderBlocker = nullptr;
    bool m_orderBlockerWrite = false;
    const sc_interface *m_orderBlockerClock = nullptr;

};

#endif /* MEMORY_BFM_H_ */
