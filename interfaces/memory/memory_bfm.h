#ifndef MEMORY_BFM_H_
#define MEMORY_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "memory_channel.h"

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

    memory_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    // One access per rising edge with enable high, as on memory_sp/memory_dp. Read
    // data is driven on the edge that samples the access and holds until the next
    // read. The Verilated model is an SC_METHOD woken by the same edge, so the RTL
    // evaluates that edge with the old read_data and sees the new value after it,
    // like a flop output.
    // request() must not consume simulated time. Edges that pass while it waits,
    // such as a tandem memory tee waiting for the model side, are not sampled.
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
                if_p->request(is_write, addr, data);
                if (!is_write) {
                    hdl_if_p->read_data = VL_DATA_T(data.sc_pack());
                }
            }
            wait(clk.posedge_event());
        }
    }

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
            if (!is_write) {
                // The RTL's registered read_data updates one delta after the edge,
                // so sampling at the edge returns the previous read's word.
                wait(SC_ZERO_TIME);
                data.sc_unpack(hdl_if_p->read_data);
            }
            hdl_if_p->enable = false;
            if (!is_write) if_p->complete(data);
            hdl_if_p->addr = VL_ADDR_T(0);
            hdl_if_p->wr_en = false;
            hdl_if_p->write_data = VL_DATA_T(0);
        }
    }

};

#endif /* MEMORY_BFM_H_ */
