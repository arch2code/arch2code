#ifndef PYSOCKET_HDL_SC_WRAPPER_H_
#define PYSOCKET_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=pySocket

#include "pySocketBase.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "pySocket_hdl_sv_wrapper.h"
#else
#include "VpySocket_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

class pySocket_hdl_sc_wrapper: public sc_module, public blockBase, public pySocketBase {

public:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "pySocket_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < pySocket_hdl_sc_wrapper > (blockName, variant, bbMode));
                });
        }
    };

    static registerBlock registerBlock_;

#if !defined(VERILATOR) && defined(VCS)
    pySocket_hdl_sv_wrapper *dut_hdl;
#else
    VpySocket_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    

    SC_HAS_PROCESS (pySocket_hdl_sc_wrapper);

    pySocket_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("pySocket_hdl_sc_wrapper", name(), bbMode),
        pySocketBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new pySocket_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VpySocket_hdl_sv_wrapper("dut_hdl");
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

#endif // PYSOCKET_HDL_SC_WRAPPER_H_
