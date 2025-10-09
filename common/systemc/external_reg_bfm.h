#ifndef EXTERNAL_REG_BFM_H_
#define EXTERNAL_REG_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "external_reg_channel.h"

template<typename VL_DATA_T>
struct external_reg_hdl_if: public sc_interface {
    sc_signal<VL_DATA_T> wdata;
    sc_signal<VL_DATA_T> rdata;
    sc_signal<sc_bv<2>>  write;
};

template<typename DATA_T, typename VL_DATA_T>
class external_reg_src_bfm: public sc_module {

public:

    external_reg_out<DATA_T> if_p;
    sc_port<external_reg_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (external_reg_src_bfm);

    external_reg_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        while (true) {
            wait(clk.posedge_event());
        }
    }

};

template<typename DATA_T, typename VL_DATA_T>
class external_reg_dst_bfm: public sc_module {

public:

    external_reg_in<DATA_T> if_p;
    sc_port<external_reg_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (external_reg_dst_bfm);

    external_reg_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        while (true) {
            wait(clk.posedge_event());
        }
    }

};

#endif /* EXTERNAL_REG_BFM_H_ */
