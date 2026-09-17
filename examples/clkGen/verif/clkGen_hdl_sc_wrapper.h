#ifndef CLKGEN_HDL_SC_WRAPPER_H_
#define CLKGEN_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=clkGen
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import clkGen.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "clkGen_hdl_sv_wrapper.h"
#else
#include "VclkGen_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "socketSync.h"
class clkGen_hdl_sc_wrapper: public sc_module, public blockBase, public clkGenBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    clkGen_hdl_sv_wrapper *dut_hdl;
#else
    VclkGen_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clkRef;
    sc_signal<bool> clkDiv;

    

    SC_HAS_PROCESS (clkGen_hdl_sc_wrapper);

    clkGen_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("clkGen_hdl_sc_wrapper", name(), bbMode),
        clkGenBase(name(), variant),
        clkRef("clkRef"),
        clkDiv("clkDiv"),
        
        rstRef_n("rstRef_n", true),
        clkRef_half_(sc_time(10, SC_NS) / 2)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new clkGen_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VclkGen_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->clkRef(clkRef);
        dut_hdl->clkDiv(clkDiv);
        dut_hdl->rstRef_n(rstRef_n);

        

        clkRef.write(true);
        SC_THREAD(clock_gen_clkRef);
        SC_THREAD(reset_driver_rstRef_n);
        SC_METHOD(clkDiv_edge_count); sensitive << clkDiv.value_changed_event(); dont_initialize();

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
        if (!clkDiv_edges_) { std::cerr << "warning: clock 'clkDiv' produced no edge by end of run" << std::endl; }
    }

private:

    

    sc_signal<bool> rstRef_n;
    sc_time clkRef_half_;
    int clkDiv_edges_ = 0;

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

    void clock_gen_clkRef() { clock_gen(clkRef, clkRef_half_); }
    void reset_driver_rstRef_n() { reset_driver(rstRef_n, clkRef, 3); }
    void clkDiv_edge_count() { clkDiv_edges_++; }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // CLKGEN_HDL_SC_WRAPPER_H_
