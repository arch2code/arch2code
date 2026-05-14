#ifndef IPLEAF_HDL_SC_WRAPPER_H_
#define IPLEAF_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=ipLeaf

#include "ipLeafBase.h"

// Verilated RTL top (SystemC)
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=variant_include_sv_wrapper_header
#if !defined(VERILATOR) && defined(VCS)
#include "ipLeaf_variantLeaf0_hdl_sv_wrapper.h"
#else
#include "VipLeaf_variantLeaf0_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

template <typename DUT_T>
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "ipLeafConfig.h"

template <typename DUT_T, typename Config>
class ipLeaf_hdl_sc_wrapper: public sc_module, public blockBase, public ipLeafBase<Config> {

public:

    struct registerBlock
    {
        registerBlock(const char *variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "ipLeaf_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < ipLeaf_hdl_sc_wrapper<DUT_T, Config> > (blockName, variant, bbMode));
                }, variant_);
        }
    };

    static registerBlock registerBlock_;

    DUT_T *dut_hdl;

    sc_clock clk;

    

    SC_HAS_PROCESS (ipLeaf_hdl_sc_wrapper<DUT_T, Config>);

    ipLeaf_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("ipLeaf_hdl_sc_wrapper", name(), bbMode),
        ipLeafBase<Config>(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        
        rst_n(0)
    {
        dut_hdl = new DUT_T("dut_hdl");

        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        

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
using ipLeaf_variantLeaf0_hdl_sc_wrapper = ipLeaf_hdl_sc_wrapper<ipLeaf_variantLeaf0_hdl_sv_wrapper, ipLeafVariantLeaf0Config>;
#else
using ipLeaf_variantLeaf0_hdl_sc_wrapper = ipLeaf_hdl_sc_wrapper<VipLeaf_variantLeaf0_hdl_sv_wrapper, ipLeafVariantLeaf0Config>;
#endif
// GENERATED_CODE_END

#endif // IPLEAF_HDL_SC_WRAPPER_H_
