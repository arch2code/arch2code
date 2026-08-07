#ifndef SIMPLE_HDL_SC_WRAPPER_H_
#define SIMPLE_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
#include "systemc.h"
#include "blockBase.h"
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

import simple;
using namespace simple_ns;
#include "push_ack_bfm.h"

class simple_hdl_sc_wrapper: public sc_module, public blockBase, public simpleBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    simple_hdl_sv_wrapper *dut_hdl;
#else
    Vsimple_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    

    SC_HAS_PROCESS (simple_hdl_sc_wrapper);

    simple_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("simple_hdl_sc_wrapper", name(), bbMode),
        simpleBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new simple_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new Vsimple_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        

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

    void reset_driver() {
        wait(5, SC_NS);
        rst_n = true;
    }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // SIMPLE_HDL_SC_WRAPPER_H_
