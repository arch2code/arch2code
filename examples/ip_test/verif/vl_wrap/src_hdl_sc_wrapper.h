#ifndef SRC_HDL_SC_WRAPPER_H_
#define SRC_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=src

#include "srcBase.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "src_hdl_sv_wrapper.h"
#else
#include "Vsrc_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "ipLeafConfig.h"
#include "srcConfig.h"
#include "push_ack_bfm.h"

template <typename DUT_T>
class src_hdl_sc_wrapper: public sc_module, public blockBase, public srcBase<srcDefaultConfig> {

public:

    struct registerBlock
    {
        registerBlock(const char *variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "src_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < src_hdl_sc_wrapper<DUT_T> > (blockName, variant, bbMode));
                }, variant_);
        }
    };

    static registerBlock registerBlock_;

    DUT_T *dut_hdl;

    sc_clock clk;

    push_ack_src_bfm<srcOut0St<srcDefaultConfig>, sc_bv<9>> out0_bfm;
    push_ack_src_bfm<srcOut1St<srcDefaultConfig>, sc_bv<71>> out1_bfm;

    SC_HAS_PROCESS (src_hdl_sc_wrapper<DUT_T>);

    src_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("src_hdl_sc_wrapper", name(), bbMode),
        srcBase<srcDefaultConfig>(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        out0_bfm("out0_bfm"),
        out1_bfm("out1_bfm"),
        rst_n(0)
    {
        dut_hdl = new DUT_T("dut_hdl");

        dut_hdl->out0_push(out0_hdl_if.push);
        dut_hdl->out0_data(out0_hdl_if.data);
        dut_hdl->out0_ack(out0_hdl_if.ack);
        dut_hdl->out1_push(out1_hdl_if.push);
        dut_hdl->out1_data(out1_hdl_if.data);
        dut_hdl->out1_ack(out1_hdl_if.ack);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        out0_bfm.if_p(out0);
        out0_bfm.hdl_if_p(out0_hdl_if);
        out0_bfm.clk(clk);
        out0_bfm.rst_n(rst_n);

        out1_bfm.if_p(out1);
        out1_bfm.hdl_if_p(out1_hdl_if);
        out1_bfm.clk(clk);
        out1_bfm.rst_n(rst_n);

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

    push_ack_hdl_if<sc_bv<9>> out0_hdl_if;
    push_ack_hdl_if<sc_bv<71>> out1_hdl_if;

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

#endif // SRC_HDL_SC_WRAPPER_H_
