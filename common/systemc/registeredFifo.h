#ifndef REGISTERED_FIFO_H
#define REGISTERED_FIFO_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "bfmContractCheck.h"
#include "q_assert.h"
#include <deque>
#include <format>
#include <string>

// A model's stand-in for an RTL FIFO whose full flag is registered, as Pro's
// rdyVldFifo is: write.rdy is ~full from a count that a pop changes at its
// clock edge, so the slot a read frees takes a write only on the clock after
// it, and a write to a full FIFO waits even when a read completes in that
// clock. An untimed sc_fifo frees the slot at once, so behind BFMs the model
// takes an input beat a clock before the RTL could.
//
// Model threads only call read() and write(); the clock lives in here. It is
// the clock of the BFM bound to clockPort's channel, the port whose RTL clock
// domain the FIFO is in. A slot read at time t is free for writes from the
// first rising edge after t. An entry is readable as soon as it is written,
// as the RTL FIFO's head is in the clock after the edge that pushes it: a
// model whose input comes from a src BFM writes on that edge. With no BFM on
// that channel, as in a model-only run, a read frees its slot at once. A
// run that has BFMs but none on that channel is logged once, as a FIFO left
// untimed where the RTL's is not.
template <typename T>
class registeredFifo {
public:
    registeredFifo(const char *name, int depth, sc_port_base &clockPort)
        : m_name(name), m_depth(depth), m_clockPort(clockPort), m_log(name) {
        Q_ASSERT_CTX(depth > 0, m_name, "registeredFifo depth must be positive");
        sc_core::sc_spawn([this]() { this->clockThread(); });
    }

    void write(const T &value) {
        while (static_cast<int>(m_data.size() + m_freedAt.size()) >= m_depth) {
            wait(m_space);
        }
        m_data.push_back(value);
        m_written.notify();
    }

    void read(T &value) {
        while (m_data.empty()) {
            wait(m_written);
        }
        value = m_data.front();
        m_data.pop_front();
        if (clock() == nullptr) {
            m_space.notify();
        } else {
            m_freedAt.push_back(sc_time_stamp());
        }
    }

    T read() {
        T value;
        read(value);
        return value;
    }

    int num_available() const { return static_cast<int>(m_data.size()); }

private:
    const sc_in<bool> *clock() {
        if (!m_resolved) {
            m_clk = bfmClocks::of(m_clockPort.get_interface());
            m_resolved = true;
            if (m_clk == nullptr && !bfmClocks::all().empty()) {
                m_log.logPrint(std::format("registeredFifo on port {}: no BFM is bound to the port's channel, so the "
                                           "FIFO frees a slot as soon as it is read, though this run has BFMs",
                                           m_clockPort.name()),
                               LOG_IMPORTANT);
            }
        }
        return m_clk;
    }

    // A read at an edge's own time frees its slot at the edge after.
    void clockThread() {
        if (clock() == nullptr) {
            return;
        }
        while (true) {
            wait(m_clk->posedge_event());
            const sc_time now = sc_time_stamp();
            bool freed = false;
            while (!m_freedAt.empty() && m_freedAt.front() < now) {
                m_freedAt.pop_front();
                freed = true;
            }
            if (freed) {
                m_space.notify();
            }
        }
    }

    const std::string m_name;
    const int m_depth;
    sc_port_base &m_clockPort;
    logBlock m_log;
    const sc_in<bool> *m_clk = nullptr;
    bool m_resolved = false;
    std::deque<T> m_data;
    std::deque<sc_time> m_freedAt;
    sc_event m_space;
    sc_event m_written;
};

#endif /* REGISTERED_FIFO_H */
