#ifndef SIMPLE_HDL_SC_WRAPPER_H_
#define SIMPLE_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import simple.base;

// Verilated RTL top (SystemC)
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

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "simple_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < simple_hdl_sc_wrapper > (blockName, variant, bbMode));
                }, "", "simple");
        }
    };

    static registerBlock registerBlock_;

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
