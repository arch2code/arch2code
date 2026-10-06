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

// HDL is external_reg src (drives write/wdata, samples rdata) — e.g. Verilated regs.
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
        hdl_if_p->rdata = VL_DATA_T(0);
        while (!rst_n) {
            wait(clk.posedge_event());
        }
        while (true) {
            wait(clk.posedge_event());
            if (!rst_n) {
                hdl_if_p->rdata = VL_DATA_T(0);
                continue;
            }

            // Drive HDL rdata from the TLM architectural mirror.
            DATA_T rdata = if_p->readNonBlocking();
            hdl_if_p->rdata = rdata.sc_pack();

            // Forward a one-cycle HDL write strobe into the TLM command path.
            if (hdl_if_p->write.read().or_reduce()) {
                DATA_T wdata;
                wdata.sc_unpack(hdl_if_p->wdata);
                if_p->reg_write_cmd(wdata);
            }
        }
    }

};

// HDL is external_reg dst (samples write/wdata, drives rdata) — e.g. Verilated dma_engine.
// SystemC regs use reg_write_cmd(); this BFM read()s those and pulses HDL.
// Architectural APB image is updated only via update_mirror (from HDL rdata).
template<typename DATA_T, typename VL_DATA_T>
class external_reg_dst_bfm: public sc_module {

public:

    external_reg_in<DATA_T> if_p;
    sc_port<external_reg_hdl_if<VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (external_reg_dst_bfm);

    external_reg_dst_bfm(sc_module_name modulename) {
        SC_THREAD(write_driver_thread);
        SC_THREAD(rdata_monitor_thread);
    }

    // CPU/regs reg_write_cmd() → one-cycle HDL write strobe.
    // update_mirror does not notify read(), so rdata publishes never re-enter here.
    void write_driver_thread() {
        hdl_if_p->write = 0;
        hdl_if_p->wdata = VL_DATA_T(0);
        while (!rst_n) {
            wait(clk.posedge_event());
        }
        while (true) {
            DATA_T data;
            if_p->read(data);

            hdl_if_p->wdata = data.sc_pack();
            hdl_if_p->write = 1; // non-zero strobe; RTL uses |write
            wait(clk.posedge_event());
            hdl_if_p->write = 0;
            // Registered rdata updates on the write edge; sample on the next clock.
            wait(clk.posedge_event());

            DATA_T rdata;
            rdata.sc_unpack(hdl_if_p->rdata);
            if_p->update_mirror(rdata);
        }
    }

    // HDL rdata → TLM mirror so APB readNonBlocking() sees live STATUS/etc.
    void rdata_monitor_thread() {
        DATA_T last{};
        bool have_last = false;
        while (!rst_n) {
            wait(clk.posedge_event());
        }
        while (true) {
            wait(clk.posedge_event());
            if (!rst_n) {
                have_last = false;
                continue;
            }

            DATA_T data;
            data.sc_unpack(hdl_if_p->rdata);
            if (!have_last || !(data == last)) {
                if_p->update_mirror(data);
                last = data;
                have_last = true;
            }
        }
    }

};

#endif /* EXTERNAL_REG_BFM_H_ */
