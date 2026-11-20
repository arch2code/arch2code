#ifndef BFMCLOCKEDGE_H
#define BFMCLOCKEDGE_H
// copyright the arch2code project contributors, see
// https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// A BFM drives a pin when a model call returns. If the call returns in the
// timestep of a clock edge, the pin must change after the clock, so that the
// RTL does not see it at that edge on any simulator. Counting deltas does not
// do this, because a clock can change in any delta of its timestep: sc_clock
// changes in the first, and the lockstep clock_gen a delta or more later.
//
// bfmClockEdge records the times of the clock's last three changes and from
// them predicts the next one. settle() returns at once unless a change is due
// in this timestep and has not happened yet. Then it waits for that change,
// and returns in the delta where the RTL samples it, so a pin written next
// changes after the edge. It returns true if it waited.
//
// This assumes the clock keeps a steady period from its fourth change.
// sc_clock and the wrapper's free-running clock are always steady.
// The gated lockstep clock is steady only between gating changes. When gating
// starts after the clock has free-run, its first gated change comes one
// lockstep step early, and when the sync link is lost the clock free-runs
// from that moment. Within the first three changes after such a step,
// settle() mispredicts twice. It can miss a change due in this timestep, so
// the RTL sees a pin at that edge, or wait for a change that is not due, which
// holds the pin to the next change. Reset is released when gating starts, so
// the first calls out of reset can fall in this window. A model stays out of
// it by making its first pin-driving call no earlier than two full clocks
// after reset release. After link loss the partner is gone, so only the local
// run is affected.
class bfmClockEdge : public sc_module {

public:

    sc_in<bool> clk;

    SC_HAS_PROCESS(bfmClockEdge);

    explicit bfmClockEdge(sc_module_name name) : sc_module(name) {
        SC_METHOD(record);
        sensitive << clk;
        dont_initialize();
    }

    bool settle() {
        if (m_seen < 3) {
            return false;
        }
        const sc_time now = sc_time_stamp();
        // record() runs in the delta after a change, so a change it has not
        // recorded yet shows as a new clock value.
        if (m_last[2] == now || clk.read() != m_value) {
            return false;
        }
        // The change before last went the same way as the next one.
        if (m_last[1] + (m_last[2] - m_last[0]) != now) {
            return false;
        }
        sc_core::wait(clk.value_changed_event());
        return true;
    }

private:

    void record() {
        m_last[0] = m_last[1];
        m_last[1] = m_last[2];
        m_last[2] = sc_time_stamp();
        m_value = clk.read();
        if (m_seen < 3) {
            m_seen++;
        }
    }

    sc_time m_last[3];
    bool m_value = false;
    int m_seen = 0;

};

#endif /* BFMCLOCKEDGE_H */
