#ifndef APB_BFM_H_
#define APB_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "apb_channel.h"

template<typename VL_ADDR_T, typename VL_DATA_T>
struct apb_hdl_if: public sc_interface {
    sc_signal<VL_ADDR_T> paddr;
    sc_signal<bool> psel;
    sc_signal<bool> penable;
    sc_signal<bool> pwrite;
    sc_signal<VL_DATA_T> pwdata;
    sc_signal<bool> pready;
    sc_signal<VL_DATA_T> prdata;
    sc_signal<bool> pslverr;
};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class apb_src_bfm: public sc_module {

public:

    apb_out<ADDR_T, DATA_T> if_p;
    sc_port<apb_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (apb_src_bfm);

    apb_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        while (true) {
            ADDR_T addr;
            DATA_T data;
            bool is_write;
            bool slverr;
            hdl_if_p->pslverr = false;
            hdl_if_p->pready = false;
            hdl_if_p->prdata = VL_DATA_T(0);
            while ( !(hdl_if_p->psel && hdl_if_p->penable )) {
                wait(clk.posedge_event());
            }
            is_write = hdl_if_p->pwrite;
            addr.sc_unpack(hdl_if_p->paddr);
            if( is_write ) {
                data.sc_unpack(hdl_if_p->pwdata);
            }
            if_p->request(is_write, addr, data);
            wait(clk.posedge_event());
            hdl_if_p->pready = true;
            if( !is_write ) {
                hdl_if_p->prdata = VL_DATA_T(data.sc_pack());
            }
            wait(clk.posedge_event());
            hdl_if_p->pslverr = false;
            hdl_if_p->pready = false;
            hdl_if_p->prdata = VL_DATA_T(0);
            while ( hdl_if_p->psel && hdl_if_p->penable ) {
              wait(clk.posedge_event());
            };
        }
    }

};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class apb_dst_bfm: public sc_module {

public:

    apb_in<ADDR_T, DATA_T> if_p;
    sc_port<apb_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (apb_dst_bfm);

    apb_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    void bfm_driver_thread() {
        while(!rst_n) wait(clk.posedge_event());
        while (true) {
            ADDR_T addr;
            DATA_T data;
            bool is_write;
            bool slverr;
            if_p->reqReceive(is_write, addr, data);
            hdl_if_p->psel = true;
            hdl_if_p->paddr = addr.sc_pack();
            if ( is_write ) {
                hdl_if_p->pwrite = true;
                hdl_if_p->pwdata = data.sc_pack();
            }
            wait(clk.posedge_event());
            hdl_if_p->penable = true;
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->pready);
            if ( !is_write ) {
                data.sc_unpack(hdl_if_p->prdata);
            }
            hdl_if_p->penable = false;
            slverr = hdl_if_p->pslverr;
            if( !is_write ) if_p->complete(data);
            hdl_if_p->psel = false;
            hdl_if_p->paddr = VL_ADDR_T(0);
            hdl_if_p->pwrite = false;
            hdl_if_p->pwdata = VL_DATA_T(0);
            Q_ASSERT(!slverr, "Unexpected slverr flag set");
        }
    }

};

#endif /* APB_BFM_H_ */
