#ifndef MEMORY_BFM_H_
#define MEMORY_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "memory_channel.h"
#include "bfmContractCheck.h"

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

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class memory_dst_bfm: public sc_module {

public:

    memory_in<ADDR_T, DATA_T> if_p;
    sc_port<memory_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (memory_dst_bfm);

    memory_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            ADDR_T addr;
            DATA_T data;
            bool is_write;
            if_p->reqReceive(is_write, addr, data);
            hdl_if_p->enable = true;
            hdl_if_p->addr = addr.sc_pack();
            if (is_write) {
                hdl_if_p->wr_en = true;
                hdl_if_p->write_data = data.sc_pack();
            } else {
                hdl_if_p->wr_en = false;
            }
            wait(clk.posedge_event());
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

};

#endif /* MEMORY_BFM_H_ */
