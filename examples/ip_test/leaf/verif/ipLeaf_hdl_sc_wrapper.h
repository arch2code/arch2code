#ifndef IPLEAF_HDL_SC_WRAPPER_H_
#define IPLEAF_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=ipLeaf
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import ip_test_ipLeaf.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

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
        clk_half_(0.5, SC_NS)
    {
        dut_hdl = new DUT_T("dut_hdl");

        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        

        clk.write(true);
        SC_THREAD(clock_gen);
        SC_THREAD(reset_driver);

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

    void clock_gen() {
        // 1 ns period, 50% duty. Under lockstep gated mode the quantum thread
        // owns timed waits; we only toggle when an edge is requested.
        while (true) {
            if (socketSyncTimeGated()) {
                socketSyncWaitClockEdge();
                clk.write(!clk.read());
            } else {
                wait(clk_half_);
                clk.write(!clk.read());
            }
        }
    }

    void reset_driver() {
        // rst_n starts deasserted so the first write(false) is a negedge.
        // Verilator async reset (@(negedge rst_n)) does not run if the pin
        // is born low and only later rises.
        // Lockstep: follow socketSyncRstN (boot release + mid-sim MSG_RESET).
        // Do not wait on clk — gated lockstep deadlocks before the first quantum.
        // Free-run / non-socket: assert, hold, then release.
        if (socketSyncLockstepEnabled()) {
            rst_n.write(socketSyncRstN());
            while (true) {
                wait(socketSyncRstNEvent());
                rst_n.write(socketSyncRstN());
            }
        } else {
            rst_n.write(false);
            wait(5, SC_NS);
            rst_n.write(true);
        }
    }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // IPLEAF_HDL_SC_WRAPPER_H_
