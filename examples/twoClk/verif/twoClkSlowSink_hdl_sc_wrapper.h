#ifndef TWOCLKSLOWSINK_HDL_SC_WRAPPER_H_
#define TWOCLKSLOWSINK_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=twoClkSlowSink
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import twoClk_twoClkSlowSink.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "twoClkSlowSink_hdl_sv_wrapper.h"
#else
#include "VtwoClkSlowSink_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import twoClkIp;
using namespace twoClkIp_ns;
#include "push_ack_bfm.h"

class twoClkSlowSink_hdl_sc_wrapper: public sc_module, public blockBase, public twoClkSlowSinkBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    twoClkSlowSink_hdl_sv_wrapper *dut_hdl;
#else
    VtwoClkSlowSink_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clkSlow;

    push_ack_dst_bfm<twoClkDataSt, sc_bv<8>> in_bfm;

    SC_HAS_PROCESS (twoClkSlowSink_hdl_sc_wrapper);

    twoClkSlowSink_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("twoClkSlowSink_hdl_sc_wrapper", name(), bbMode),
        twoClkSlowSinkBase(name(), variant),
        clkSlow("clkSlow", sc_time(3, SC_NS), 0.5, sc_time(3, SC_NS), true),
        in_bfm("in_bfm"),
        rstSlow_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new twoClkSlowSink_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VtwoClkSlowSink_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->in_push(in_hdl_if.push);
        dut_hdl->in_data(in_hdl_if.data);
        dut_hdl->in_ack(in_hdl_if.ack);
        dut_hdl->clkSlow(clkSlow);
        dut_hdl->rstSlow_n(rstSlow_n);

        in_bfm.if_p(this->in);
        in_bfm.hdl_if_p(in_hdl_if);
        in_bfm.clk(clkSlow);
        in_bfm.rst_n(rstSlow_n);

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

    push_ack_hdl_if<sc_bv<8>> in_hdl_if;

    sc_signal<bool> rstSlow_n;

    void reset_driver_rstSlow_n() {
        for (int cycle = 0; cycle < 3; cycle++) {
            wait(clkSlow.posedge_event());
        }
        rstSlow_n = true;
    }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // TWOCLKSLOWSINK_HDL_SC_WRAPPER_H_
