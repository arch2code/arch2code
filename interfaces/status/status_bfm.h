#ifndef STATUS_BFM_H_
#define STATUS_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "status_channel.h"

template<typename VL_DATA_T>
struct status_hdl_if: public sc_interface {
    sc_signal<VL_DATA_T> data;
};

template<typename DATA_T, typename VL_DATA_T>
class status_src_bfm: public sc_module {

public:

    status_out<DATA_T> if_p;
    sc_port<status_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (status_src_bfm);

    status_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        while (true) {
            DATA_T data;
            wait(clk.posedge_event());
            data.sc_unpack(hdl_if_p->data);
            if_p->write(data);
        }
    }

};

template<typename DATA_T, typename VL_DATA_T>
class status_dst_bfm: public sc_module {

public:

    status_in<DATA_T> if_p;
    sc_port<status_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (status_dst_bfm);

    status_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        while (true) {
            DATA_T data;
            if_p->read(data);
            hdl_if_p->data = data.sc_pack();
            wait(clk.posedge_event());
        }
    }

};

#endif /* STATUS_BFM_H_ */
