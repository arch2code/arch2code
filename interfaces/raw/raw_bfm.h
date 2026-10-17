#ifndef RAW_BFM_H_
#define RAW_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "raw_channel.h"
#include "bfmContractCheck.h"

template<typename VL_DATA_T>
struct raw_hdl_if: public sc_interface {
    sc_signal<VL_DATA_T> data;
};

template<typename DATA_T, typename VL_DATA_T>
class raw_src_bfm: public sc_module {

public:

    raw_out<DATA_T> if_p;
    sc_port<raw_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (raw_src_bfm);

    raw_src_bfm(sc_module_name modulename) :
        m_missed(name(), "SystemC had not taken the previous raw word at a clock edge, so the word on that edge was lost", "clock edges") {
        SC_THREAD(bfm_driver_thread);
        SC_METHOD(edge_monitor);
        sensitive << clk.pos();
        dont_initialize();
    }

    virtual void end_of_simulation() {
        m_missed.report();
    }

    void bfm_driver_thread() {
        DATA_T data;
        while (true) {
            wait(clk.posedge_event());
            data.sc_unpack(hdl_if_p->data);
            m_sampleTime = sc_time_stamp();
            m_writing = true;
            if_p->write(data);
            m_writing = false;
            m_readerStarted = true;
            // The next wait cannot see an edge in this delta. edge_monitor has
            // counted that edge only if it ran first.
            if (clk.posedge() && m_lastMiss != sc_time_stamp()) {
                missed();
            }
        }
    }

    // An edge that passes while the write blocks loses its word. Edges before
    // the reader's first read do not count, because a reader may start late.
    void edge_monitor() {
        if (m_writing && m_readerStarted && sc_time_stamp() > m_sampleTime) {
            missed();
        }
    }

private:

    void missed() {
        m_lastMiss = sc_time_stamp();
        m_missed.fail(m_lastMiss);
    }

    bool m_writing = false;
    bool m_readerStarted = false;
    sc_time m_sampleTime;
    sc_time m_lastMiss;
    bfmContractCheck m_missed;

};

template<typename DATA_T, typename VL_DATA_T>
class raw_dst_bfm: public sc_module {

public:

    raw_in<DATA_T> if_p;
    sc_port<raw_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (raw_dst_bfm);

    raw_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        DATA_T data;
        while (true) {
            if_p->read(data);
            hdl_if_p->data = data.sc_pack();
            wait(clk.posedge_event());
        }
    }

};

#endif /* RAW_BFM_H_ */
