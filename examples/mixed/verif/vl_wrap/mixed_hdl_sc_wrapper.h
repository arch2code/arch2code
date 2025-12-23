#ifndef MIXED_HDL_SC_WRAPPER_H_
#define MIXED_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=mixed

#include "mixedBase.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "mixed_hdl_sv_wrapper.h"
#else
#include "Vmixed_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "apb_bfm.h"
#include "notify_ack_bfm.h"
#include "rdy_vld_bfm.h"
#include "req_ack_bfm.h"

class mixed_hdl_sc_wrapper: public sc_module, public blockBase, public mixedBase {

public:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "mixed_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < mixed_hdl_sc_wrapper > (blockName, variant, bbMode));
                });
        }
    };

    static registerBlock registerBlock_;

#if !defined(VERILATOR) && defined(VCS)
    mixed_hdl_sv_wrapper *dut_hdl;
#else
    Vmixed_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    apb_dst_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> cpu_main_bfm;

    SC_HAS_PROCESS (mixed_hdl_sc_wrapper);

    mixed_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("mixed_hdl_sc_wrapper", name(), bbMode),
        mixedBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        cpu_main_bfm("cpu_main_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new mixed_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new Vmixed_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->cpu_main_paddr(cpu_main_hdl_if.paddr);
        dut_hdl->cpu_main_psel(cpu_main_hdl_if.psel);
        dut_hdl->cpu_main_penable(cpu_main_hdl_if.penable);
        dut_hdl->cpu_main_pwrite(cpu_main_hdl_if.pwrite);
        dut_hdl->cpu_main_pwdata(cpu_main_hdl_if.pwdata);
        dut_hdl->cpu_main_pready(cpu_main_hdl_if.pready);
        dut_hdl->cpu_main_prdata(cpu_main_hdl_if.prdata);
        dut_hdl->cpu_main_pslverr(cpu_main_hdl_if.pslverr);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        cpu_main_bfm.if_p(cpu_main);
        cpu_main_bfm.hdl_if_p(cpu_main_hdl_if);
        cpu_main_bfm.clk(clk);
        cpu_main_bfm.rst_n(rst_n);

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

    apb_hdl_if<sc_bv<32>, sc_bv<32>> cpu_main_hdl_if;

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

#endif // MIXED_HDL_SC_WRAPPER_H_
