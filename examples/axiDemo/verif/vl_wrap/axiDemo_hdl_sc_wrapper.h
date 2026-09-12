#ifndef AXIDEMO_HDL_SC_WRAPPER_H_
#define AXIDEMO_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=axiDemo
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import axiDemo.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "axiDemo_hdl_sv_wrapper.h"
#else
#include "VaxiDemo_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#ifdef VERILATOR
#include "verilated_vcd_c.h"
#endif
import axiDemo;
using namespace axiDemo_ns;
#include "axi4_stream_bfm.h"
#include "axi_read_bfm.h"
#include "axi_write_bfm.h"

#include "socketSync.h"
class axiDemo_hdl_sc_wrapper: public sc_module, public blockBase, public axiDemoBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    axiDemo_hdl_sv_wrapper *dut_hdl;
#else
    VaxiDemo_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    

    SC_HAS_PROCESS (axiDemo_hdl_sc_wrapper);

    axiDemo_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("axiDemo_hdl_sc_wrapper", name(), bbMode),
        axiDemoBase(name(), variant),
        clk("clk"),
        
        rst_n("rst_n", true),
        clk_half_(0.5, SC_NS)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new axiDemo_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VaxiDemo_hdl_sv_wrapper("dut_hdl");
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

#endif // AXIDEMO_HDL_SC_WRAPPER_H_
