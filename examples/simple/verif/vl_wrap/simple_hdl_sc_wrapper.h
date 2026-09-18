#ifndef SIMPLE_HDL_SC_WRAPPER_H_
#define SIMPLE_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import simple.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "simple_hdl_sv_wrapper.h"
#else
#include "Vsimple_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#ifdef VERILATOR
#include "verilated_vcd_c.h"
#endif
import simple;
using namespace simple_ns;
#include "push_ack_bfm.h"

#include "socketSync.h"
class simple_hdl_sc_wrapper: public sc_module, public blockBase, public simpleBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    simple_hdl_sv_wrapper *dut_hdl;
#else
    Vsimple_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    

    SC_HAS_PROCESS (simple_hdl_sc_wrapper);

    simple_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("simple_hdl_sc_wrapper", name(), bbMode),
        simpleBase(name(), variant),
        clk("clk"),
        
        rst_n("rst_n", true),
        clk_half_(0.5, SC_NS)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new simple_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new Vsimple_hdl_sv_wrapper("dut_hdl");
#endif

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
        // Only when pysocket_sync is connected; otherwise no partner releases rst_n.
        // Free-run / non-socket: assert, hold, then release.
        if (socketSyncLockstepActive()) {
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

#endif // SIMPLE_HDL_SC_WRAPPER_H_
