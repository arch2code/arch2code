#ifndef XPRTNESTDECODE_HDL_SC_WRAPPER_H_
#define XPRTNESTDECODE_HDL_SC_WRAPPER_H_

// GENERATED_CODE_PARAM --block=xpRtNestDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
#include "systemc.h"
#include "blockBase.h"
import xpRtInh_xpRtNestDecode.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import common_shared_types;
using namespace common_shared_types_ns;
import xpRtInh;
using namespace xpRtInh_ns;
import xpRtInh.xpRtNestDecode.config;
#include "apb_bfm.h"

template <typename DUT_T, typename Config>
class xpRtNestDecode_hdl_sc_wrapper: public sc_module, public blockBase, public xpRtNestDecodeBase<Config> {

public:

    DUT_T *dut_hdl;

    sc_clock clk;

    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_uLeaf_bfm;
    apb_dst_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_bfm;

    // SC_HAS_PROCESS expects a single macro argument; the Config-templated
    // self type carries a comma in its argument list and must be aliased.
    using xpRtNestDecode_hdl_sc_wrapper_self_t = xpRtNestDecode_hdl_sc_wrapper<DUT_T, Config>;
    SC_HAS_PROCESS (xpRtNestDecode_hdl_sc_wrapper_self_t);

    xpRtNestDecode_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("xpRtNestDecode_hdl_sc_wrapper", name(), bbMode),
        xpRtNestDecodeBase<Config>(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        apbReg_uLeaf_bfm("apbReg_uLeaf_bfm"),
        apbReg_bfm("apbReg_bfm"),
        rst_n(0)
    {
        dut_hdl = new DUT_T("dut_hdl");

        dut_hdl->apbReg_uLeaf_paddr(apbReg_uLeaf_hdl_if.paddr);
        dut_hdl->apbReg_uLeaf_psel(apbReg_uLeaf_hdl_if.psel);
        dut_hdl->apbReg_uLeaf_penable(apbReg_uLeaf_hdl_if.penable);
        dut_hdl->apbReg_uLeaf_pwrite(apbReg_uLeaf_hdl_if.pwrite);
        dut_hdl->apbReg_uLeaf_pwdata(apbReg_uLeaf_hdl_if.pwdata);
        dut_hdl->apbReg_uLeaf_pready(apbReg_uLeaf_hdl_if.pready);
        dut_hdl->apbReg_uLeaf_prdata(apbReg_uLeaf_hdl_if.prdata);
        dut_hdl->apbReg_uLeaf_pslverr(apbReg_uLeaf_hdl_if.pslverr);
        dut_hdl->apbReg_paddr(apbReg_hdl_if.paddr);
        dut_hdl->apbReg_psel(apbReg_hdl_if.psel);
        dut_hdl->apbReg_penable(apbReg_hdl_if.penable);
        dut_hdl->apbReg_pwrite(apbReg_hdl_if.pwrite);
        dut_hdl->apbReg_pwdata(apbReg_hdl_if.pwdata);
        dut_hdl->apbReg_pready(apbReg_hdl_if.pready);
        dut_hdl->apbReg_prdata(apbReg_hdl_if.prdata);
        dut_hdl->apbReg_pslverr(apbReg_hdl_if.pslverr);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        apbReg_uLeaf_bfm.if_p(this->apbReg_uLeaf);
        apbReg_uLeaf_bfm.hdl_if_p(apbReg_uLeaf_hdl_if);
        apbReg_uLeaf_bfm.clk(clk);
        apbReg_uLeaf_bfm.rst_n(rst_n);

        apbReg_bfm.if_p(this->apbReg);
        apbReg_bfm.hdl_if_p(apbReg_hdl_if);
        apbReg_bfm.clk(clk);
        apbReg_bfm.rst_n(rst_n);

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

    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_uLeaf_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_hdl_if;

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

#endif // XPRTNESTDECODE_HDL_SC_WRAPPER_H_
