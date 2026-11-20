#ifndef RDY_VLD_SRC_DRIVER_H_
#define RDY_VLD_SRC_DRIVER_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include <functional>
#include "systemc.h"
#include "rdy_vld_channel.h"

// One rdy/vld lane a src BFM receives from the RTL. Ready is high only while
// the model waits in read(). A beat the RTL holds with ready low is offered,
// so a model that reads only an active port sees it, and is withdrawn when
// reset or the RTL drops it. The driver offers a beat at the falling edge
// after the RTL raises vld, so a model that reads it then raises ready in time
// for the next rising edge. The RTL's outputs from the rising edge have
// settled half a clock later, and the protocol holds vld and the data until
// the handshake.
//
// A read() wakes the driver in the read's delta, which can be the delta in
// which a rising edge changes the clock. Ready driven in that delta reaches
// Verilator at that edge, but Xcelium and VCS sample the edge first. So the
// driver raises ready a delta later, after the edge's processes have run,
// and the RTL sees it at the next edge on every simulator.
//
// The falling-edge offer assumes vld and the data come from flops on this
// clock's rising edge. An output with a combinational path from an input
// driven in that timestep, or launched by another clock such as one the DUT
// divides, is offered at the next rising edge instead, and that timing may
// differ by simulator. Data and order do not change, because the take samples
// the wires again at the rising edge.
template <class T>
class rdyVldSrcDriver {

public:

    rdyVldSrcDriver(sc_port<rdy_vld_out_if<T>> &ch, sc_in<bool> &clk, sc_in<bool> &rst_n,
                    sc_signal<bool> &vld, sc_signal<bool> &rdy, std::function<void(T &)> unpack) :
        m_ch(ch), m_clk(clk), m_rst_n(rst_n), m_vld(vld), m_rdy(rdy), m_unpack(unpack) {}

    // The BFM calls this from a method on both clock edges. An edge with vld
    // high and ready low leaves the beat with the RTL. It only reads the
    // wires, so a second call in the same delta changes nothing.
    void sampleEdge() {
        m_held = m_rst_n.read() && m_vld.read() && !m_rdy.read();
        if (m_held) {
            m_unpack(m_heldBeat);
        }
    }

    void waitOutReset() {
        m_rdy = false;
        while (!m_rst_n.read()) {
            wait(m_clk.posedge_event());
        }
    }

    // take() sends a beat the RTL handed over to the model. inReset() runs on
    // an edge in reset and returns true once it has waited the reset out. An
    // empty inReset goes on with the edge, where only a handshake moves a beat.
    void run(std::function<void(T &)> take, std::function<bool()> inReset) {
        T data;
        bool offered = false;
        m_rdy = m_ch->get_rdy();
        while (true) {
            wait(m_clk.posedge_event() | m_clk.negedge_event() | m_ch->readEnteredEvent());
            if (!m_clk.event()) {
                // A read() woke the driver. An edge in this timestep has run
                // its processes by the next delta, and is handled below.
                wait(SC_ZERO_TIME);
            }
            if (m_clk.negedge()) {
                if (m_rst_n && m_vld && !m_rdy && !offered) {
                    m_unpack(data);
                    m_ch->offer(data);
                    offered = true;
                } else if (offered && !m_vld) {
                    // The RTL dropped an offered beat with no handshake.
                    m_ch->withdraw();
                    offered = false;
                }
                m_rdy = m_ch->get_rdy();
                continue;
            }
            if (!m_clk.posedge()) {
                m_rdy = m_ch->get_rdy();
                continue;
            }
            bool live = m_rst_n.read();
            if (live && offered && !m_vld) {
                // The RTL dropped an offered beat with no handshake.
                m_ch->withdraw();
                offered = false;
            }
            if (!live) {
                if (offered) {
                    m_ch->withdraw();
                    offered = false;
                }
                if (inReset && inReset()) {
                    m_rdy = m_ch->get_rdy();
                    continue;
                }
            }
            if (m_vld && m_rdy) {
                m_unpack(data);
                // The RTL must not transfer while a delayed send blocks.
                m_rdy = false;
                take(data);
                // A send that returns in an edge's delta may run before the
                // method samples that edge. The wires still show the values
                // the edge sampled, so sample it here.
                if (m_clk.event()) {
                    sampleEdge();
                }
                // An edge that passed while the send blocked left the next
                // beat with the RTL.
                offered = m_held;
                if (offered) {
                    m_ch->offer(m_heldBeat);
                }
            } else if (m_vld && live && !offered) {
                m_unpack(data);
                m_ch->offer(data);
                offered = true;
            }
            m_rdy = m_ch->get_rdy();
        }
    }

private:

    sc_port<rdy_vld_out_if<T>> &m_ch;
    sc_in<bool> &m_clk;
    sc_in<bool> &m_rst_n;
    sc_signal<bool> &m_vld;
    sc_signal<bool> &m_rdy;
    std::function<void(T &)> m_unpack;
    bool m_held = false;
    T m_heldBeat;

};

#endif /* RDY_VLD_SRC_DRIVER_H_ */
