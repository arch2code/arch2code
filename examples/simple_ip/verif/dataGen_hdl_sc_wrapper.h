#ifndef DATAGEN_HDL_SC_WRAPPER_H_
#define DATAGEN_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=dataGen
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import simple_ip_dataGen.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "dataGen_hdl_sv_wrapper.h"
#else
#include "VdataGen_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import simple_ip;
using namespace simple_ip_ns;
#include "push_ack_bfm.h"

#include "socketSync.h"
class dataGen_hdl_sc_wrapper: public sc_module, public blockBase, public dataGenBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    dataGen_hdl_sv_wrapper *dut_hdl;
#else
    VdataGen_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    push_ack_src_bfm<simpleData8St, sc_bv<9>> out_bfm;

    SC_HAS_PROCESS (dataGen_hdl_sc_wrapper);

    dataGen_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("dataGen_hdl_sc_wrapper", name(), bbMode),
        dataGenBase(name(), variant),
        clk("clk"),
        out_bfm("out_bfm"),
        rst_n("rst_n", true),
        clk_half_(sc_time(1, SC_NS) / 2)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new dataGen_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VdataGen_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->out_push(out_hdl_if.push);
        dut_hdl->out_data(out_hdl_if.data);
        dut_hdl->out_ack(out_hdl_if.ack);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        out_bfm.if_p(this->out);
        out_bfm.hdl_if_p(out_hdl_if);
        out_bfm.clk(clk);
        out_bfm.rst_n(rst_n);

        clk.write(true);
        SC_THREAD(clock_gen_clk);
        SC_THREAD(reset_driver_rst_n);

        end_ctor_init();

    }

public:

#ifdef VERILATOR
    void vl_trace(VerilatedVcdC* tfp, int levels, int options = 0) override {
        dut_hdl->trace(tfp, levels, options);
    }
#endif

private:

    push_ack_hdl_if<sc_bv<9>> out_hdl_if;

    sc_signal<bool> rst_n;
    sc_time clk_half_;

    // Free-run: toggle every half period. Gated lockstep: the quantum thread
    // broadcasts one edge request per socketSyncClockHalfPeriod() of advanced
    // time, and a clock toggles once its own half period has accumulated, so a
    // slower clock keeps its period at quantum resolution and no clock can
    // free-run during wait(ack).
    void clock_gen(sc_signal<bool> &sig, const sc_time &half) {
        sc_time gated = SC_ZERO_TIME;
        while (true) {
            if (socketSyncTimeGated()) {
                socketSyncWaitClockEdge();
                gated += socketSyncClockHalfPeriod();
                if (gated >= half) {
                    gated -= half;
                    sig.write(!sig.read());
                }
            } else {
                wait(half);
                sig.write(!sig.read());
            }
        }
    }

    // Lockstep with a connected partner: follow socketSyncRstN (boot release
    // and mid-sim MSG_RESET) and never wait on a clock, since gated time does
    // not advance before the first quantum. Otherwise assert, hold for the
    // declared releaseCycles edges of the reset's own clock, then release.
    void reset_driver(sc_signal<bool> &rst, sc_signal<bool> &clk, int cycles) {
        if (socketSyncLockstepActive()) {
            rst.write(socketSyncRstN());
            while (true) {
                wait(socketSyncRstNEvent());
                rst.write(socketSyncRstN());
            }
        } else {
            rst.write(false);
            for (int cycle = 0; cycle < cycles; cycle++) {
                wait(clk.posedge_event());
            }
            rst.write(true);
        }
    }

    void clock_gen_clk() { clock_gen(clk, clk_half_); }
    void reset_driver_rst_n() { reset_driver(rst_n, clk, 3); }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // DATAGEN_HDL_SC_WRAPPER_H_
