#ifndef APBDECODE_HDL_SC_WRAPPER_H_
#define APBDECODE_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=apbDecode

#include "apbDecodeBase.h"

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

    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apb_uIp0_bfm;
    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apb_uIp1_bfm;
    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apb_uBridge_bfm;
    apb_dst_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> cpu_main_bfm;

    SC_HAS_PROCESS (apbDecode_hdl_sc_wrapper);

    apbDecode_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("apbDecode_hdl_sc_wrapper", name(), bbMode),
        apbDecodeBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        apb_uIp0_bfm("apb_uIp0_bfm"),
        apb_uIp1_bfm("apb_uIp1_bfm"),
        apb_uBridge_bfm("apb_uBridge_bfm"),
        cpu_main_bfm("cpu_main_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new apbDecode_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VapbDecode_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->apb_uIp0_paddr(apb_uIp0_hdl_if.paddr);
        dut_hdl->apb_uIp0_psel(apb_uIp0_hdl_if.psel);
        dut_hdl->apb_uIp0_penable(apb_uIp0_hdl_if.penable);
        dut_hdl->apb_uIp0_pwrite(apb_uIp0_hdl_if.pwrite);
        dut_hdl->apb_uIp0_pwdata(apb_uIp0_hdl_if.pwdata);
        dut_hdl->apb_uIp0_pready(apb_uIp0_hdl_if.pready);
        dut_hdl->apb_uIp0_prdata(apb_uIp0_hdl_if.prdata);
        dut_hdl->apb_uIp0_pslverr(apb_uIp0_hdl_if.pslverr);
        dut_hdl->apb_uIp1_paddr(apb_uIp1_hdl_if.paddr);
        dut_hdl->apb_uIp1_psel(apb_uIp1_hdl_if.psel);
        dut_hdl->apb_uIp1_penable(apb_uIp1_hdl_if.penable);
        dut_hdl->apb_uIp1_pwrite(apb_uIp1_hdl_if.pwrite);
        dut_hdl->apb_uIp1_pwdata(apb_uIp1_hdl_if.pwdata);
        dut_hdl->apb_uIp1_pready(apb_uIp1_hdl_if.pready);
        dut_hdl->apb_uIp1_prdata(apb_uIp1_hdl_if.prdata);
        dut_hdl->apb_uIp1_pslverr(apb_uIp1_hdl_if.pslverr);
        dut_hdl->apb_uBridge_paddr(apb_uBridge_hdl_if.paddr);
        dut_hdl->apb_uBridge_psel(apb_uBridge_hdl_if.psel);
        dut_hdl->apb_uBridge_penable(apb_uBridge_hdl_if.penable);
        dut_hdl->apb_uBridge_pwrite(apb_uBridge_hdl_if.pwrite);
        dut_hdl->apb_uBridge_pwdata(apb_uBridge_hdl_if.pwdata);
        dut_hdl->apb_uBridge_pready(apb_uBridge_hdl_if.pready);
        dut_hdl->apb_uBridge_prdata(apb_uBridge_hdl_if.prdata);
        dut_hdl->apb_uBridge_pslverr(apb_uBridge_hdl_if.pslverr);
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

        apb_uIp0_bfm.if_p(apb_uIp0);
        apb_uIp0_bfm.hdl_if_p(apb_uIp0_hdl_if);
        apb_uIp0_bfm.clk(clk);
        apb_uIp0_bfm.rst_n(rst_n);

        apb_uIp1_bfm.if_p(apb_uIp1);
        apb_uIp1_bfm.hdl_if_p(apb_uIp1_hdl_if);
        apb_uIp1_bfm.clk(clk);
        apb_uIp1_bfm.rst_n(rst_n);

        apb_uBridge_bfm.if_p(apb_uBridge);
        apb_uBridge_bfm.hdl_if_p(apb_uBridge_hdl_if);
        apb_uBridge_bfm.clk(clk);
        apb_uBridge_bfm.rst_n(rst_n);

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

    apb_hdl_if<sc_bv<32>, sc_bv<32>> apb_uIp0_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apb_uIp1_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apb_uBridge_hdl_if;
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

#endif // APBDECODE_HDL_SC_WRAPPER_H_
