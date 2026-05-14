#ifndef IP_HDL_SC_WRAPPER_H_
#define IP_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=ip

#include "ipBase.h"

// Verilated RTL top (SystemC)
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=variant_include_sv_wrapper_header
#if !defined(VERILATOR) && defined(VCS)
#include "ip_variant0_hdl_sv_wrapper.h"
#include "ip_variant1_hdl_sv_wrapper.h"
#else
#include "Vip_variant0_hdl_sv_wrapper.h"
#include "Vip_variant1_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "ipConfig.h"
#include "apb_bfm.h"
#include "push_ack_bfm.h"

template <typename DUT_T>
class ip_hdl_sc_wrapper: public sc_module, public blockBase, public ipBase<srcDefaultConfig> {

public:

    struct registerBlock
    {
        registerBlock(const char *variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "ip_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < ip_hdl_sc_wrapper<DUT_T> > (blockName, variant, bbMode));
                }, variant_);
        }
    };

    static registerBlock registerBlock_;

    DUT_T *dut_hdl;

    sc_clock clk;

    push_ack_dst_bfm<ipDataSt<srcDefaultConfig>, sc_bv<71>> ipDataIf_bfm;
    apb_dst_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_bfm;

    SC_HAS_PROCESS (ip_hdl_sc_wrapper<DUT_T>);

    ip_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("ip_hdl_sc_wrapper", name(), bbMode),
        ipBase<srcDefaultConfig>(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        ipDataIf_bfm("ipDataIf_bfm"),
        apbReg_bfm("apbReg_bfm"),
        rst_n(0)
    {
        dut_hdl = new DUT_T("dut_hdl");

        dut_hdl->ipDataIf_push(ipDataIf_hdl_if.push);
        dut_hdl->ipDataIf_data(ipDataIf_hdl_if.data);
        dut_hdl->ipDataIf_ack(ipDataIf_hdl_if.ack);
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

        ipDataIf_bfm.if_p(ipDataIf);
        ipDataIf_bfm.hdl_if_p(ipDataIf_hdl_if);
        ipDataIf_bfm.clk(clk);
        ipDataIf_bfm.rst_n(rst_n);

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

    push_ack_hdl_if<sc_bv<71>> ipDataIf_hdl_if;
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

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=variant_class_template_spec
#if !defined(VERILATOR) && defined(VCS)
using ip_variant0_hdl_sc_wrapper = ip_hdl_sc_wrapper<ip_variant0_hdl_sv_wrapper>;
using ip_variant1_hdl_sc_wrapper = ip_hdl_sc_wrapper<ip_variant1_hdl_sv_wrapper>;
#else
using ip_variant0_hdl_sc_wrapper = ip_hdl_sc_wrapper<Vip_variant0_hdl_sv_wrapper>;
using ip_variant1_hdl_sc_wrapper = ip_hdl_sc_wrapper<Vip_variant1_hdl_sv_wrapper>;
#endif
// GENERATED_CODE_END

#endif // IP_HDL_SC_WRAPPER_H_
