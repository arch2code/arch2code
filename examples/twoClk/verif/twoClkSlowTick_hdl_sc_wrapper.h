#ifndef TWOCLKSLOWTICK_HDL_SC_WRAPPER_H_
#define TWOCLKSLOWTICK_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=twoClkSlowTick
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import twoClk_twoClkSlowTick.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "twoClkSlowTick_hdl_sv_wrapper.h"
#else
#include "VtwoClkSlowTick_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import twoClkIp;
using namespace twoClkIp_ns;
#include "push_ack_bfm.h"

#include "socketSync.h"
class twoClkSlowTick_hdl_sc_wrapper: public sc_module, public blockBase, public twoClkSlowTickBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    twoClkSlowTick_hdl_sv_wrapper *dut_hdl;
#else
    VtwoClkSlowTick_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clkSlow;

    push_ack_src_bfm<twoClkDataSt, sc_bv<8>> out_bfm;

    SC_HAS_PROCESS (twoClkSlowTick_hdl_sc_wrapper);

    twoClkSlowTick_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("twoClkSlowTick_hdl_sc_wrapper", name(), bbMode),
        twoClkSlowTickBase(name(), variant),
        clkSlow("clkSlow"),
        out_bfm("out_bfm"),
        rstSlow_n("rstSlow_n", true),
        clkSlow_half_(sc_time(3, SC_NS) / 2)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new twoClkSlowTick_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VtwoClkSlowTick_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->out_push(out_hdl_if.push);
        dut_hdl->out_data(out_hdl_if.data);
        dut_hdl->out_ack(out_hdl_if.ack);
        dut_hdl->clkSlow(clkSlow);
        dut_hdl->rstSlow_n(rstSlow_n);

        out_bfm.if_p(this->out);
        out_bfm.hdl_if_p(out_hdl_if);
        out_bfm.clk(clkSlow);
        out_bfm.rst_n(rstSlow_n);

        clkSlow.write(true);
        SC_THREAD(clock_gen_clkSlow);
        SC_THREAD(reset_driver_rstSlow_n);

        end_ctor_init();

    }

public:

#ifdef VERILATOR
    void vl_trace(VerilatedVcdC* tfp, int levels, int options = 0) override {
        dut_hdl->trace(tfp, levels, options);
    }
#endif

private:

    push_ack_hdl_if<sc_bv<8>> out_hdl_if;

    sc_signal<bool> rstSlow_n;
    sc_time clkSlow_half_;

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

    void clock_gen_clkSlow() { clock_gen(clkSlow, clkSlow_half_); }
    void reset_driver_rstSlow_n() { reset_driver(rstSlow_n, clkSlow, 3); }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // TWOCLKSLOWTICK_HDL_SC_WRAPPER_H_
