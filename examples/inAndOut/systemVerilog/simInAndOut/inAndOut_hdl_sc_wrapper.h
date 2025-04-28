#ifndef INANDOUT_HDL_SC_WRAPPER_H_
#define INANDOUT_HDL_SC_WRAPPER_H_

#include "systemc.h"

#include "instanceFactory.h"

#include "rdy_vld_bfm.h"

#include "req_ack_bfm.h"
#include "pop_ack_bfm.h"
#include "apb_bfm.h"

// GENERATED_CODE_PARAM --block=inAndOut

#include "inAndOut_base.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "inAndOut_hdl_sv_wrapper.h"
#else
#include "VinAndOut_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "pop_ack_bfm.h"
#include "rdy_vld_bfm.h"
#include "req_ack_bfm.h"

class inAndOut_hdl_sc_wrapper: public sc_module, public blockBase, public inAndOutBase {

public:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "inAndOut_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < inAndOut_hdl_sc_wrapper > (blockName, variant, bbMode));
                });
        }
    };

    static registerBlock registerBlock_;

#if !defined(VERILATOR) && defined(VCS)
    inAndOut_hdl_sv_wrapper *dut_hdl;
#else
    VinAndOut_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    rdy_vld_src_bfm<aSt, sc_bv<2>> aOut_bfm;
    rdy_vld_dst_bfm<aSt, sc_bv<2>> aIn_bfm;
    req_ack_src_bfm<bSt, bBSt, sc_bv<5>, bool> bOut_bfm;
    req_ack_dst_bfm<bSt, bBSt, sc_bv<5>, bool> bIn_bfm;
    pop_ack_src_bfm<dSt, sc_bv<7>> dOut_bfm;
    pop_ack_dst_bfm<dSt, sc_bv<7>> dIn_bfm;

    SC_HAS_PROCESS (inAndOut_hdl_sc_wrapper);

    inAndOut_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("inAndOut_hdl_sc_wrapper", name(), bbMode),
        inAndOutBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        aOut_bfm("aOut_bfm"),
        aIn_bfm("aIn_bfm"),
        bOut_bfm("bOut_bfm"),
        bIn_bfm("bIn_bfm"),
        dOut_bfm("dOut_bfm"),
        dIn_bfm("dIn_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new inAndOut_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VinAndOut_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->aOut_vld(aOut_hdl_if.vld);
        dut_hdl->aOut_data(aOut_hdl_if.data);
        dut_hdl->aOut_rdy(aOut_hdl_if.rdy);
        dut_hdl->aIn_vld(aIn_hdl_if.vld);
        dut_hdl->aIn_data(aIn_hdl_if.data);
        dut_hdl->aIn_rdy(aIn_hdl_if.rdy);
        dut_hdl->bOut_req(bOut_hdl_if.req);
        dut_hdl->bOut_data(bOut_hdl_if.data);
        dut_hdl->bOut_ack(bOut_hdl_if.ack);
        dut_hdl->bOut_rdata(bOut_hdl_if.rdata);
        dut_hdl->bIn_req(bIn_hdl_if.req);
        dut_hdl->bIn_data(bIn_hdl_if.data);
        dut_hdl->bIn_ack(bIn_hdl_if.ack);
        dut_hdl->bIn_rdata(bIn_hdl_if.rdata);
        dut_hdl->dOut_pop(dOut_hdl_if.pop);
        dut_hdl->dOut_ack(dOut_hdl_if.ack);
        dut_hdl->dOut_rdata(dOut_hdl_if.rdata);
        dut_hdl->dIn_pop(dIn_hdl_if.pop);
        dut_hdl->dIn_ack(dIn_hdl_if.ack);
        dut_hdl->dIn_rdata(dIn_hdl_if.rdata);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        aOut_bfm.if_p(aOut);
        aOut_bfm.hdl_if_p(aOut_hdl_if);
        aOut_bfm.clk(clk);
        aOut_bfm.rst_n(rst_n);

        aIn_bfm.if_p(aIn);
        aIn_bfm.hdl_if_p(aIn_hdl_if);
        aIn_bfm.clk(clk);
        aIn_bfm.rst_n(rst_n);

        bOut_bfm.if_p(bOut);
        bOut_bfm.hdl_if_p(bOut_hdl_if);
        bOut_bfm.clk(clk);
        bOut_bfm.rst_n(rst_n);

        bIn_bfm.if_p(bIn);
        bIn_bfm.hdl_if_p(bIn_hdl_if);
        bIn_bfm.clk(clk);
        bIn_bfm.rst_n(rst_n);

        dOut_bfm.if_p(dOut);
        dOut_bfm.hdl_if_p(dOut_hdl_if);
        dOut_bfm.clk(clk);
        dOut_bfm.rst_n(rst_n);

        dIn_bfm.if_p(dIn);
        dIn_bfm.hdl_if_p(dIn_hdl_if);
        dIn_bfm.clk(clk);
        dIn_bfm.rst_n(rst_n);

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

    rdy_vld_hdl_if<sc_bv<2>> aOut_hdl_if;
    rdy_vld_hdl_if<sc_bv<2>> aIn_hdl_if;
    req_ack_hdl_if<sc_bv<5>, bool> bOut_hdl_if;
    req_ack_hdl_if<sc_bv<5>, bool> bIn_hdl_if;
    pop_ack_hdl_if<sc_bv<7>> dOut_hdl_if;
    pop_ack_hdl_if<sc_bv<7>> dIn_hdl_if;

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

#endif // INANDOUT_HDL_SC_WRAPPER_H_
