#ifndef BLOCKF_HDL_SC_WRAPPER_H_
#define BLOCKF_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import mixed_blockF.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import mixed_mixedBlockC;
using namespace mixed_mixedBlockC_ns;
import mixed;
using namespace mixed_ns;
#include "mixedVariantConfig.h"
#include "rdy_vld_bfm.h"
#include "status_bfm.h"

template <typename DUT_T, typename Config>
class blockF_hdl_sc_wrapper: public sc_module, public blockBase, public blockFBase<Config> {

public:

    DUT_T *dut_hdl;

    sc_clock clk;

    rdy_vld_src_bfm<seeSt, sc_bv<5>> cStuffIf_bfm;
    rdy_vld_dst_bfm<dSt, sc_bv<7>> dStuffIf_bfm;
    rdy_vld_dst_bfm<dSt, sc_bv<7>> dSin_bfm;
    rdy_vld_src_bfm<dSt, sc_bv<7>> dSout_bfm;
    status_dst_bfm<dRegSt, sc_bv<7>> rwD_bfm;

    // SC_HAS_PROCESS expects a single macro argument; the Config-templated
    // self type carries a comma in its argument list and must be aliased.
    using blockF_hdl_sc_wrapper_self_t = blockF_hdl_sc_wrapper<DUT_T, Config>;
    SC_HAS_PROCESS (blockF_hdl_sc_wrapper_self_t);

    blockF_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("blockF_hdl_sc_wrapper", name(), bbMode),
        blockFBase<Config>(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        cStuffIf_bfm("cStuffIf_bfm"),
        dStuffIf_bfm("dStuffIf_bfm"),
        dSin_bfm("dSin_bfm"),
        dSout_bfm("dSout_bfm"),
        rwD_bfm("rwD_bfm"),
        rst_n(0)
    {
        dut_hdl = new DUT_T("dut_hdl");

        dut_hdl->cStuffIf_vld(cStuffIf_hdl_if.vld);
        dut_hdl->cStuffIf_data(cStuffIf_hdl_if.data);
        dut_hdl->cStuffIf_rdy(cStuffIf_hdl_if.rdy);
        dut_hdl->dStuffIf_vld(dStuffIf_hdl_if.vld);
        dut_hdl->dStuffIf_data(dStuffIf_hdl_if.data);
        dut_hdl->dStuffIf_rdy(dStuffIf_hdl_if.rdy);
        dut_hdl->dSin_vld(dSin_hdl_if.vld);
        dut_hdl->dSin_data(dSin_hdl_if.data);
        dut_hdl->dSin_rdy(dSin_hdl_if.rdy);
        dut_hdl->dSout_vld(dSout_hdl_if.vld);
        dut_hdl->dSout_data(dSout_hdl_if.data);
        dut_hdl->dSout_rdy(dSout_hdl_if.rdy);
        dut_hdl->rwD_data(rwD_hdl_if.data);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        cStuffIf_bfm.if_p(this->cStuffIf);
        cStuffIf_bfm.hdl_if_p(cStuffIf_hdl_if);
        cStuffIf_bfm.clk(clk);
        cStuffIf_bfm.rst_n(rst_n);

        dStuffIf_bfm.if_p(this->dStuffIf);
        dStuffIf_bfm.hdl_if_p(dStuffIf_hdl_if);
        dStuffIf_bfm.clk(clk);
        dStuffIf_bfm.rst_n(rst_n);

        dSin_bfm.if_p(this->dSin);
        dSin_bfm.hdl_if_p(dSin_hdl_if);
        dSin_bfm.clk(clk);
        dSin_bfm.rst_n(rst_n);

        dSout_bfm.if_p(this->dSout);
        dSout_bfm.hdl_if_p(dSout_hdl_if);
        dSout_bfm.clk(clk);
        dSout_bfm.rst_n(rst_n);

        rwD_bfm.if_p(this->rwD);
        rwD_bfm.hdl_if_p(rwD_hdl_if);
        rwD_bfm.clk(clk);
        rwD_bfm.rst_n(rst_n);

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
    rdy_vld_hdl_if<sc_bv<7>> dSin_hdl_if;
    rdy_vld_hdl_if<sc_bv<7>> dSout_hdl_if;
    status_hdl_if<sc_bv<7>> rwD_hdl_if;

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

#endif // BLOCKF_HDL_SC_WRAPPER_H_
