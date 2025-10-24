#ifndef RDY_VLD_BFM_H_
#define RDY_VLD_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "rdy_vld_channel.h"

template<typename VL_DATA_T>
struct rdy_vld_hdl_if: public sc_interface {
    sc_signal<bool> vld;
    sc_signal<VL_DATA_T> data;
    sc_signal<bool> rdy;
};

template<typename DATA_T, typename VL_DATA_T>
class rdy_vld_src_bfm: public sc_module {

public:

    rdy_vld_out<DATA_T> if_p;
    sc_port<rdy_vld_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (rdy_vld_src_bfm);

    rdy_vld_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    virtual void end_of_elaboration() {
        if_p->setCycleTransaction();
    }

    void bfm_driver_thread() {
        DATA_T data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->rdy = if_p->get_rdy();
            while (!(hdl_if_p->vld && hdl_if_p->rdy)) {
                wait(clk.posedge_event());
                hdl_if_p->rdy = if_p->get_rdy();
            }
            data.sc_unpack(hdl_if_p->data);
            if_p->writeClocked(data);
            wait(clk.posedge_event());
        }
    }

};

template<typename DATA_T, typename VL_DATA_T>
class rdy_vld_dst_bfm: public sc_module {

public:

    rdy_vld_in<DATA_T> if_p;
    sc_port<rdy_vld_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (rdy_vld_dst_bfm);

    ::sc_core::sc_process_handle rdy_control_thread_handle;

    rdy_vld_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
        //SC_METHOD(rdy_control_thread);
        rdy_control_thread_handle =
            sc_core::sc_get_curr_simcontext()->create_method_process("rdy_control_thread", false,
                static_cast<sc_core::SC_ENTRY_FUNC>(&SC_CURRENT_USER_MODULE::rdy_control_thread), this, 0);
    }

    virtual void end_of_elaboration() {
        //this->sensitive << rdy_control_thread_handle <<  hdl_if_p->rdy;
        //if_p->enable_user_ready_control(); // delayed until here to ensure the port is bound
        if_p->setCycleTransaction();
    }

    void bfm_driver_thread() {
        DATA_T data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->vld = 0;
            hdl_if_p->data = VL_DATA_T(0);
            if_p->readClocked(data);
            hdl_if_p->vld = 1;
            hdl_if_p->data = data.sc_pack();
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->rdy);
        }
    }

    void rdy_control_thread() {
        if_p->set_rdy(hdl_if_p->rdy);
    }

};

#endif /* RDY_VLD_BFM_H_ */
