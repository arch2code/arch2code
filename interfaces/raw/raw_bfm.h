#ifndef RAW_BFM_H_
#define RAW_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "raw_channel.h"

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

    raw_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        DATA_T data;
        while (true) {
            wait(clk.posedge_event());
            data.sc_unpack(hdl_if_p->data);
            if_p->write(data);
        }
    }

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
