#ifndef RSTSYNC_HDL_SC_WRAPPER_H_
#define RSTSYNC_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=rstSync
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import clkGen_rstSync.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "rstSync_hdl_sv_wrapper.h"
#else
#include "VrstSync_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#ifdef VERILATOR
#include "verilated_vcd_c.h"
#endif

#include "socketSync.h"
class rstSync_hdl_sc_wrapper: public sc_module, public blockBase, public rstSyncBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    rstSync_hdl_sv_wrapper *dut_hdl;
#else
    VrstSync_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    

    SC_HAS_PROCESS (rstSync_hdl_sc_wrapper);

    rstSync_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("rstSync_hdl_sc_wrapper", name(), bbMode),
        rstSyncBase(name(), variant),
        clk("clk"),
        rstIn_n("rstIn_n", true),
        rstOut_n("rstOut_n", true),
        clk_half_(sc_time(20, SC_NS) / 2)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new rstSync_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VrstSync_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->clk(clk);
        dut_hdl->rstIn_n(rstIn_n);
        dut_hdl->rstOut_n(rstOut_n);

        

        clk.write(true);
        SC_THREAD(clock_gen_clk);
        SC_THREAD(reset_driver_rstIn_n);
        SC_METHOD(rstOut_n_release_track); sensitive << rstOut_n.value_changed_event(); dont_initialize();

        end_ctor_init();

    }

public:

#ifdef VERILATOR
    void vl_trace(VerilatedVcdC* tfp, int levels, int options = 0) override {
        dut_hdl->trace(tfp, levels, options);
    }
#endif

    // R23: reported at end of run rather than left to a silent,
    // activity-free run (spec §4.8).
    void end_of_simulation() override {
        if (!rstOut_n_released_) { std::cerr << "warning: output reset 'rstOut_n' was never observed to release during the run" << std::endl; }
    }

private:

    

    sc_signal<bool> rstIn_n;
    sc_signal<bool> rstOut_n;
    sc_time clk_half_;
    bool rstOut_n_released_ = false;

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
    // The clock parameter is named reset_driver_clk, not clk: a block whose
    // own default clock is literally named clk declares a same-named member,
    // which a parameter named clk would otherwise shadow (-Wshadow).
    void reset_driver(sc_signal<bool> &rst, sc_signal<bool> &reset_driver_clk, int cycles) {
        if (socketSyncLockstepActive()) {
            rst.write(socketSyncRstN());
            while (true) {
                wait(socketSyncRstNEvent());
                rst.write(socketSyncRstN());
            }
        } else {
            rst.write(false);
            for (int cycle = 0; cycle < cycles; cycle++) {
                wait(reset_driver_clk.posedge_event());
            }
            rst.write(true);
        }
    }

    void clock_gen_clk() { clock_gen(clk, clk_half_); }
    void reset_driver_rstIn_n() { reset_driver(rstIn_n, clk, 3); }
    void rstOut_n_release_track() { if (rstOut_n.read()) rstOut_n_released_ = true; }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // RSTSYNC_HDL_SC_WRAPPER_H_
