#ifndef VLILEAF_HDL_SC_WRAPPER_H_
#define VLILEAF_HDL_SC_WRAPPER_H_

// GENERATED_CODE_PARAM --block=vliLeaf
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
#include "systemc.h"
#include "blockBase.h"
import vlInh_vliLeaf.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import vlInh_vliCont;
using namespace vlInh_vliCont_ns;
#include "vliContVariantConfig.h"
#include "push_ack_bfm.h"

template <typename DUT_T, typename Config>
class vliLeaf_hdl_sc_wrapper: public sc_module, public blockBase, public vliLeafBase<Config> {

public:

    DUT_T *dut_hdl;

    sc_clock clk;

    push_ack_src_bfm<vliSt<Config>, sc_bv<vliSt<Config>::_bitWidth>> out_bfm;
    push_ack_dst_bfm<vliSt<Config>, sc_bv<vliSt<Config>::_bitWidth>> in_bfm;

    // SC_HAS_PROCESS expects a single macro argument; the Config-templated
    // self type carries a comma in its argument list and must be aliased.
    using vliLeaf_hdl_sc_wrapper_self_t = vliLeaf_hdl_sc_wrapper<DUT_T, Config>;
    SC_HAS_PROCESS (vliLeaf_hdl_sc_wrapper_self_t);

    vliLeaf_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("vliLeaf_hdl_sc_wrapper", name(), bbMode),
        vliLeafBase<Config>(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        out_bfm("out_bfm"),
        in_bfm("in_bfm"),
        rst_n(0)
    {
        dut_hdl = new DUT_T("dut_hdl");

        dut_hdl->out_push(out_hdl_if.push);
        dut_hdl->out_data(out_hdl_if.data);
        dut_hdl->out_ack(out_hdl_if.ack);
        dut_hdl->in_push(in_hdl_if.push);
        dut_hdl->in_data(in_hdl_if.data);
        dut_hdl->in_ack(in_hdl_if.ack);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        out_bfm.if_p(this->out);
        out_bfm.hdl_if_p(out_hdl_if);
        out_bfm.clk(clk);
        out_bfm.rst_n(rst_n);

        in_bfm.if_p(this->in);
        in_bfm.hdl_if_p(in_hdl_if);
        in_bfm.clk(clk);
        in_bfm.rst_n(rst_n);

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

    push_ack_hdl_if<sc_bv<vliSt<Config>::_bitWidth>> out_hdl_if;
    push_ack_hdl_if<sc_bv<vliSt<Config>::_bitWidth>> in_hdl_if;

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

#endif // VLILEAF_HDL_SC_WRAPPER_H_
