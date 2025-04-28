#ifndef BLOCKF_HDL_SC_WRAPPER_H_
#define BLOCKF_HDL_SC_WRAPPER_H_

#include "systemc.h"

#include "instanceFactory.h"


// GENERATED_CODE_PARAM --block=blockF

#include "blockF_base.h"

// Verilated RTL top (SystemC)
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=variant_include_sv_wrapper_header
#if !defined(VERILATOR) && defined(VCS)
#include "blockF_variant0_hdl_sv_wrapper.h"
#include "blockF_variant1_hdl_sv_wrapper.h"
#else
#include "VblockF_variant0_hdl_sv_wrapper.h"
#include "VblockF_variant1_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "rdy_vld_bfm.h"

template <typename DUT_T>
class blockF_hdl_sc_wrapper: public sc_module, public blockBase, public blockFBase {

public:

    struct registerBlock
    {
        registerBlock(const char *variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "blockF_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < blockF_hdl_sc_wrapper<DUT_T> > (blockName, variant, bbMode));
                }, variant_);
        }
    };

    static registerBlock registerBlock_;

    DUT_T *dut_hdl;

    sc_clock clk;

    rdy_vld_src_bfm<seeSt, sc_bv<5>> cStuffIf_bfm;
    rdy_vld_dst_bfm<dSt, sc_bv<7>> dStuffIf_bfm;

    SC_HAS_PROCESS (blockF_hdl_sc_wrapper<DUT_T>);

    blockF_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("blockF_hdl_sc_wrapper", name(), bbMode),
        blockFBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        cStuffIf_bfm("cStuffIf_bfm"),
        dStuffIf_bfm("dStuffIf_bfm"),
        rst_n(0)
    {
        dut_hdl = new DUT_T("dut_hdl");

        dut_hdl->cStuffIf_vld(cStuffIf_hdl_if.vld);
        dut_hdl->cStuffIf_data(cStuffIf_hdl_if.data);
        dut_hdl->cStuffIf_rdy(cStuffIf_hdl_if.rdy);
        dut_hdl->dStuffIf_vld(dStuffIf_hdl_if.vld);
        dut_hdl->dStuffIf_data(dStuffIf_hdl_if.data);
        dut_hdl->dStuffIf_rdy(dStuffIf_hdl_if.rdy);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        cStuffIf_bfm.if_p(cStuffIf);
        cStuffIf_bfm.hdl_if_p(cStuffIf_hdl_if);
        cStuffIf_bfm.clk(clk);
        cStuffIf_bfm.rst_n(rst_n);

        dStuffIf_bfm.if_p(dStuffIf);
        dStuffIf_bfm.hdl_if_p(dStuffIf_hdl_if);
        dStuffIf_bfm.clk(clk);
        dStuffIf_bfm.rst_n(rst_n);

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

    rdy_vld_hdl_if<sc_bv<5>> cStuffIf_hdl_if;
    rdy_vld_hdl_if<sc_bv<7>> dStuffIf_hdl_if;

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

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=variant_class_template_spec
#if !defined(VERILATOR) && defined(VCS)
using blockF_variant0_hdl_sc_wrapper = blockF_hdl_sc_wrapper<blockF_variant0_hdl_sv_wrapper>;
using blockF_variant1_hdl_sc_wrapper = blockF_hdl_sc_wrapper<blockF_variant1_hdl_sv_wrapper>;
#else
using blockF_variant0_hdl_sc_wrapper = blockF_hdl_sc_wrapper<VblockF_variant0_hdl_sv_wrapper>;
using blockF_variant1_hdl_sc_wrapper = blockF_hdl_sc_wrapper<VblockF_variant1_hdl_sv_wrapper>;
#endif
// GENERATED_CODE_END

#endif // BLOCKF_HDL_SC_WRAPPER_H_
