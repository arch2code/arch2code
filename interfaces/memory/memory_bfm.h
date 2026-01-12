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

    void bfm_driver_thread() {
        while (true) {
            ADDR_T addr;
            DATA_T data;
            bool is_write;
            hdl_if_p->read_data = VL_DATA_T(0);
            while (!hdl_if_p->enable) {
                wait(clk.posedge_event());
            }
            is_write = hdl_if_p->wr_en;
            addr.sc_unpack(hdl_if_p->addr);
            if (is_write) {
                data.sc_unpack(hdl_if_p->write_data);
            }
            if_p->request(is_write, addr, data);
            wait(clk.posedge_event());
            if (!is_write) {
                hdl_if_p->read_data = VL_DATA_T(data.sc_pack());
            }
            wait(clk.posedge_event());
            hdl_if_p->read_data = VL_DATA_T(0);
            while (hdl_if_p->enable) {
                wait(clk.posedge_event());
            };
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
        while(!rst_n) wait(clk.posedge_event());
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
