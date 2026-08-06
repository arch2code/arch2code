#ifndef SOMERAPPER_HDL_SC_WRAPPER_H_
#define SOMERAPPER_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import apbDecode_someRapper.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "someRapper_hdl_sv_wrapper.h"
#else
#include "VsomeRapper_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import apbDecode;
using namespace apbDecode_ns;
#include "apb_bfm.h"

#include "socketSync.h"
class someRapper_hdl_sc_wrapper: public sc_module, public blockBase, public someRapperBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    someRapper_hdl_sv_wrapper *dut_hdl;
#else
    VsomeRapper_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    apb_dst_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_bfm;

    SC_HAS_PROCESS (someRapper_hdl_sc_wrapper);

    someRapper_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("someRapper_hdl_sc_wrapper", name(), bbMode),
        someRapperBase(name(), variant),
        clk("clk"),
        apbReg_bfm("apbReg_bfm"),
        rst_n(0),
        clk_half_(0.5, SC_NS)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new someRapper_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VsomeRapper_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->apbReg_paddr(apbReg_hdl_if.paddr);
        dut_hdl->apbReg_psel(apbReg_hdl_if.psel);
        dut_hdl->apbReg_penable(apbReg_hdl_if.penable);
        dut_hdl->apbReg_pwrite(apbReg_hdl_if.pwrite);
        dut_hdl->apbReg_pwdata(apbReg_hdl_if.pwdata);
        dut_hdl->apbReg_pready(apbReg_hdl_if.pready);
        dut_hdl->apbReg_prdata(apbReg_hdl_if.prdata);
        dut_hdl->apbReg_pslverr(apbReg_hdl_if.pslverr);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        apbReg_bfm.if_p(this->apbReg);
        apbReg_bfm.hdl_if_p(apbReg_hdl_if);
        apbReg_bfm.clk(clk);
        apbReg_bfm.rst_n(rst_n);

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

    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_hdl_if;

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
        for (int i = 0; i < 5; ++i) {
            wait(clk.posedge_event());
        }
        rst_n = true;
    }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // SOMERAPPER_HDL_SC_WRAPPER_H_
