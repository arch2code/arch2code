#ifndef TWOCLK_HDL_SC_WRAPPER_H_
#define TWOCLK_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=twoClk
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import twoClk.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "twoClk_hdl_sv_wrapper.h"
#else
#include "VtwoClk_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#ifdef VERILATOR
#include "verilated_vcd_c.h"
#endif
import twoClk;
using namespace twoClk_ns;
import twoClkIp;
using namespace twoClkIp_ns;
#include "apb_bfm.h"
#include "push_ack_bfm.h"

#include "socketSync.h"
class twoClk_hdl_sc_wrapper: public sc_module, public blockBase, public twoClkBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    twoClk_hdl_sv_wrapper *dut_hdl;
#else
    VtwoClk_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;
    sc_signal<bool> clkSlow;

    apb_dst_bfm<twoClkRegAddrSt, twoClkRegDataSt, sc_bv<32>, sc_bv<32>> twoClkReg_bfm;

    SC_HAS_PROCESS (twoClk_hdl_sc_wrapper);

    twoClk_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("twoClk_hdl_sc_wrapper", name(), bbMode),
        twoClkBase(name(), variant),
        clk("clk"),
        clkSlow("clkSlow"),
        twoClkReg_bfm("twoClkReg_bfm"),
        rst_n("rst_n", true),
        rstSlow_n("rstSlow_n", true),
        clk_half_(sc_time(1, SC_NS) / 2),
        clkSlow_half_(sc_time(3, SC_NS) / 2)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new twoClk_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VtwoClk_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->twoClkReg_paddr(twoClkReg_hdl_if.paddr);
        dut_hdl->twoClkReg_psel(twoClkReg_hdl_if.psel);
        dut_hdl->twoClkReg_penable(twoClkReg_hdl_if.penable);
        dut_hdl->twoClkReg_pwrite(twoClkReg_hdl_if.pwrite);
        dut_hdl->twoClkReg_pwdata(twoClkReg_hdl_if.pwdata);
        dut_hdl->twoClkReg_pready(twoClkReg_hdl_if.pready);
        dut_hdl->twoClkReg_prdata(twoClkReg_hdl_if.prdata);
        dut_hdl->twoClkReg_pslverr(twoClkReg_hdl_if.pslverr);
        dut_hdl->clk(clk);
        dut_hdl->clkSlow(clkSlow);
        dut_hdl->rst_n(rst_n);
        dut_hdl->rstSlow_n(rstSlow_n);

        twoClkReg_bfm.if_p(this->twoClkReg);
        twoClkReg_bfm.hdl_if_p(twoClkReg_hdl_if);
        twoClkReg_bfm.clk(clk);
        twoClkReg_bfm.rst_n(rst_n);

        clk.write(true);
        clkSlow.write(true);
        SC_THREAD(clock_gen_clk);
        SC_THREAD(clock_gen_clkSlow);
        SC_THREAD(reset_driver_rst_n);
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

    apb_hdl_if<sc_bv<32>, sc_bv<32>> twoClkReg_hdl_if;

    sc_signal<bool> rst_n;
    sc_signal<bool> rstSlow_n;
    sc_time clk_half_;
    sc_time clkSlow_half_;

    // Free-run: toggle every half period until gated lockstep begins; gating
    // only ever switches on. Gated lockstep: the quantum thread broadcasts one
    // edge request per socketSyncClockHalfPeriod() of advanced time, and a
    // clock toggles once its own half period has accumulated, so a slower
    // clock keeps its period at quantum resolution and no clock can free-run
    // during wait(ack). A half period that is not a whole number of lockstep
    // steps would be silently moved onto the step grid, so it is fatal on entry
    // to gated mode.
    void clock_gen(sc_signal<bool> &sig, const sc_time &half) {
        while (!socketSyncTimeGated()) {
            wait(half);
            sig.write(!sig.read());
        }
        const sc_time step = socketSyncClockHalfPeriod();
        Q_ASSERT(half.value() % step.value() == 0,
                 std::string("clock ") + sig.name() + " half period "
                 + half.to_string() + " is not a whole multiple of the lockstep step "
                 + step.to_string() + "; lockstep co-simulation cannot represent it. "
                 "Declare a period that is a whole multiple of " + (step + step).to_string()
                 + ", or set PYSOCKET_LOCKSTEP=0 to run free-running.");
        sc_time gated = SC_ZERO_TIME;
        while (true) {
            socketSyncWaitClockEdge();
            gated += step;
            if (gated >= half) {
                gated -= half;
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
    void clock_gen_clkSlow() { clock_gen(clkSlow, clkSlow_half_); }
    void reset_driver_rst_n() { reset_driver(rst_n, clk, 3); }
    void reset_driver_rstSlow_n() { reset_driver(rstSlow_n, clkSlow, 3); }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // TWOCLK_HDL_SC_WRAPPER_H_
