#ifndef APBDECODE_HDL_SC_WRAPPER_H_
#define APBDECODE_HDL_SC_WRAPPER_H_

#include "systemc.h"

#include "instanceFactory.h"

#include "rdy_vld_bfm.h"
#include "req_ack_bfm.h"
#include "pop_ack_bfm.h"
#include "apb_bfm.h"

// GENERATED_CODE_PARAM --block=apbDecode

#include "apbDecode_base.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "apbDecode_hdl_sv_wrapper.h"
#else
#include "VapbDecode_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "apb_bfm.h"

class apbDecode_hdl_sc_wrapper: public sc_module, public blockBase, public apbDecodeBase {

public:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "apbDecode_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < apbDecode_hdl_sc_wrapper > (blockName, variant, bbMode));
                });
        }
    };

    static registerBlock registerBlock_;

#if !defined(VERILATOR) && defined(VCS)
    apbDecode_hdl_sv_wrapper *dut_hdl;
#else
    VapbDecode_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apb_uBlockA_bfm;
    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apb_uBlockB_bfm;
    apb_dst_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_bfm;

    SC_HAS_PROCESS (apbDecode_hdl_sc_wrapper);

    apbDecode_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("apbDecode_hdl_sc_wrapper", name(), bbMode),
        apbDecodeBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        apb_uBlockA_bfm("apb_uBlockA_bfm"),
        apb_uBlockB_bfm("apb_uBlockB_bfm"),
        apbReg_bfm("apbReg_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new apbDecode_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VapbDecode_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->apb_uBlockA_paddr(apb_uBlockA_hdl_if.paddr);
        dut_hdl->apb_uBlockA_psel(apb_uBlockA_hdl_if.psel);
        dut_hdl->apb_uBlockA_penable(apb_uBlockA_hdl_if.penable);
        dut_hdl->apb_uBlockA_pwrite(apb_uBlockA_hdl_if.pwrite);
        dut_hdl->apb_uBlockA_pwdata(apb_uBlockA_hdl_if.pwdata);
        dut_hdl->apb_uBlockA_pready(apb_uBlockA_hdl_if.pready);
        dut_hdl->apb_uBlockA_prdata(apb_uBlockA_hdl_if.prdata);
        dut_hdl->apb_uBlockA_pslverr(apb_uBlockA_hdl_if.pslverr);
        dut_hdl->apb_uBlockB_paddr(apb_uBlockB_hdl_if.paddr);
        dut_hdl->apb_uBlockB_psel(apb_uBlockB_hdl_if.psel);
        dut_hdl->apb_uBlockB_penable(apb_uBlockB_hdl_if.penable);
        dut_hdl->apb_uBlockB_pwrite(apb_uBlockB_hdl_if.pwrite);
        dut_hdl->apb_uBlockB_pwdata(apb_uBlockB_hdl_if.pwdata);
        dut_hdl->apb_uBlockB_pready(apb_uBlockB_hdl_if.pready);
        dut_hdl->apb_uBlockB_prdata(apb_uBlockB_hdl_if.prdata);
        dut_hdl->apb_uBlockB_pslverr(apb_uBlockB_hdl_if.pslverr);
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

        apb_uBlockA_bfm.if_p(apb_uBlockA);
        apb_uBlockA_bfm.hdl_if_p(apb_uBlockA_hdl_if);
        apb_uBlockA_bfm.clk(clk);
        apb_uBlockA_bfm.rst_n(rst_n);

        apb_uBlockB_bfm.if_p(apb_uBlockB);
        apb_uBlockB_bfm.hdl_if_p(apb_uBlockB_hdl_if);
        apb_uBlockB_bfm.clk(clk);
        apb_uBlockB_bfm.rst_n(rst_n);

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

    apb_hdl_if<sc_bv<32>, sc_bv<32>> apb_uBlockA_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apb_uBlockB_hdl_if;
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

#endif // APBDECODE_HDL_SC_WRAPPER_H_
