#ifndef BLOCKA_HDL_SC_WRAPPER_H_
#define BLOCKA_HDL_SC_WRAPPER_H_

#include "systemc.h"

#include "instanceFactory.h"



// GENERATED_CODE_PARAM --block=blockA

#include "blockA_base.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "blockA_hdl_sv_wrapper.h"
#else
#include "VblockA_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "apb_bfm.h"
#include "notify_ack_bfm.h"
#include "rdy_vld_bfm.h"
#include "req_ack_bfm.h"

class blockA_hdl_sc_wrapper: public sc_module, public blockBase, public blockABase {

public:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "blockA_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < blockA_hdl_sc_wrapper > (blockName, variant, bbMode));
                });
        }
    };

    static registerBlock registerBlock_;

#if !defined(VERILATOR) && defined(VCS)
    blockA_hdl_sv_wrapper *dut_hdl;
#else
    VblockA_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    req_ack_src_bfm<aSt, aASt, sc_bv<4>, bool> aStuffIf_bfm;
    rdy_vld_src_bfm<seeSt, sc_bv<5>> cStuffIf_bfm;
    notify_ack_src_bfm<> startDone_bfm;
    apb_dst_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_bfm;

    SC_HAS_PROCESS (blockA_hdl_sc_wrapper);

    blockA_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("blockA_hdl_sc_wrapper", name(), bbMode),
        blockABase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        aStuffIf_bfm("aStuffIf_bfm"),
        cStuffIf_bfm("cStuffIf_bfm"),
        startDone_bfm("startDone_bfm"),
        apbReg_bfm("apbReg_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new blockA_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VblockA_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->aStuffIf_req(aStuffIf_hdl_if.req);
        dut_hdl->aStuffIf_data(aStuffIf_hdl_if.data);
        dut_hdl->aStuffIf_ack(aStuffIf_hdl_if.ack);
        dut_hdl->aStuffIf_rdata(aStuffIf_hdl_if.rdata);
        dut_hdl->cStuffIf_vld(cStuffIf_hdl_if.vld);
        dut_hdl->cStuffIf_data(cStuffIf_hdl_if.data);
        dut_hdl->cStuffIf_rdy(cStuffIf_hdl_if.rdy);
        dut_hdl->startDone_notify(startDone_hdl_if.notify);
        dut_hdl->startDone_ack(startDone_hdl_if.ack);
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

        aStuffIf_bfm.if_p(aStuffIf);
        aStuffIf_bfm.hdl_if_p(aStuffIf_hdl_if);
        aStuffIf_bfm.clk(clk);
        aStuffIf_bfm.rst_n(rst_n);

        cStuffIf_bfm.if_p(cStuffIf);
        cStuffIf_bfm.hdl_if_p(cStuffIf_hdl_if);
        cStuffIf_bfm.clk(clk);
        cStuffIf_bfm.rst_n(rst_n);

        startDone_bfm.if_p(startDone);
        startDone_bfm.hdl_if_p(startDone_hdl_if);
        startDone_bfm.clk(clk);
        startDone_bfm.rst_n(rst_n);

        apbReg_bfm.if_p(apbReg);
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

    req_ack_hdl_if<sc_bv<4>, bool> aStuffIf_hdl_if;
    rdy_vld_hdl_if<sc_bv<5>> cStuffIf_hdl_if;
    notify_ack_hdl_if<> startDone_hdl_if;
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

#endif // BLOCKA_HDL_SC_WRAPPER_H_
