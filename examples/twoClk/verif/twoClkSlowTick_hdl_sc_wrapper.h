#ifndef TWOCLKSLOWTICK_HDL_SC_WRAPPER_H_
#define TWOCLKSLOWTICK_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=twoClkSlowTick
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import twoClk_twoClkSlowTick.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "twoClkSlowTick_hdl_sv_wrapper.h"
#else
#include "VtwoClkSlowTick_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

class twoClkSlowTick_hdl_sc_wrapper: public sc_module, public blockBase, public twoClkSlowTickBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    twoClkSlowTick_hdl_sv_wrapper *dut_hdl;
#else
    VtwoClkSlowTick_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clkSlow;

    

    SC_HAS_PROCESS (twoClkSlowTick_hdl_sc_wrapper);

    twoClkSlowTick_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("twoClkSlowTick_hdl_sc_wrapper", name(), bbMode),
        twoClkSlowTickBase(name(), variant),
        clkSlow("clkSlow", sc_time(3, SC_NS), 0.5, sc_time(3, SC_NS), true),
        
        rstSlow_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new twoClkSlowTick_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VtwoClkSlowTick_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->clkSlow(clkSlow);
        dut_hdl->rstSlow_n(rstSlow_n);

        

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

#endif // TWOCLKSLOWTICK_HDL_SC_WRAPPER_H_
