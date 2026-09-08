#ifndef TWOCLKSINK_HDL_SC_WRAPPER_H_
#define TWOCLKSINK_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=twoClkSink
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import twoClk_twoClkSink.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "twoClkSink_hdl_sv_wrapper.h"
#else
#include "VtwoClkSink_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import twoClkIp;
using namespace twoClkIp_ns;
#include "push_ack_bfm.h"

class twoClkSink_hdl_sc_wrapper: public sc_module, public blockBase, public twoClkSinkBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    twoClkSink_hdl_sv_wrapper *dut_hdl;
#else
    VtwoClkSink_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    push_ack_dst_bfm<twoClkDataSt, sc_bv<8>> in_bfm;

    SC_HAS_PROCESS (twoClkSink_hdl_sc_wrapper);

    twoClkSink_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("twoClkSink_hdl_sc_wrapper", name(), bbMode),
        twoClkSinkBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        in_bfm("in_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new twoClkSink_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VtwoClkSink_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->in_push(in_hdl_if.push);
        dut_hdl->in_data(in_hdl_if.data);
        dut_hdl->in_ack(in_hdl_if.ack);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        in_bfm.if_p(this->in);
        in_bfm.hdl_if_p(in_hdl_if);
        in_bfm.clk(clk);
        in_bfm.rst_n(rst_n);

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

    push_ack_hdl_if<sc_bv<8>> in_hdl_if;

    sc_signal<bool> rst_n;

    void reset_driver_rst_n() {
        for (int cycle = 0; cycle < 3; cycle++) {
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

#endif // TWOCLKSINK_HDL_SC_WRAPPER_H_
