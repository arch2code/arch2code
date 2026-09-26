#ifndef IPLEAF_HDL_SC_WRAPPER_H_
#define IPLEAF_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=ipLeaf
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import ip_test_ipLeaf.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#ifdef VERILATOR
#include "verilated_vcd_c.h"
#endif
import ip_test_ipLeaf;
using namespace ip_test_ipLeaf_ns;
#include "ipLeafVariantConfig.h"

#include "socketSync.h"
template <typename DUT_T, typename Config>
class ipLeaf_hdl_sc_wrapper: public sc_module, public blockBase, public ipLeafBase<Config> {

public:

    DUT_T *dut_hdl;

    sc_signal<bool> clk;

    

    // SC_HAS_PROCESS expects a single macro argument; the Config-templated
    // self type carries a comma in its argument list and must be aliased.
    using ipLeaf_hdl_sc_wrapper_self_t = ipLeaf_hdl_sc_wrapper<DUT_T, Config>;
    SC_HAS_PROCESS (ipLeaf_hdl_sc_wrapper_self_t);

    ipLeaf_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("ipLeaf_hdl_sc_wrapper", name(), bbMode),
        ipLeafBase<Config>(name(), variant),
        clk("clk"),
        rst_n("rst_n", true),
        clk_half_(sc_time(1, SC_NS) / 2)
    {
        dut_hdl = new DUT_T("dut_hdl");

        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        

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

    

    sc_signal<bool> rst_n;
    sc_time clk_half_;

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
    void reset_driver_rst_n() { reset_driver(rst_n, clk, 3); }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // IPLEAF_HDL_SC_WRAPPER_H_
