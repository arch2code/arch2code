#ifndef BRIDGEDRIVER_HDL_SC_WRAPPER_H_
#define BRIDGEDRIVER_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=bridgeDriver

#include "bridgeDriverBase.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "bridgeDriver_hdl_sv_wrapper.h"
#else
#include "VbridgeDriver_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "push_ack_bfm.h"

class bridgeDriver_hdl_sc_wrapper: public sc_module, public blockBase, public bridgeDriverBase {

public:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "bridgeDriver_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < bridgeDriver_hdl_sc_wrapper > (blockName, variant, bbMode));
                });
        }
    };

    static registerBlock registerBlock_;

#if !defined(VERILATOR) && defined(VCS)
    bridgeDriver_hdl_sv_wrapper *dut_hdl;
#else
    VbridgeDriver_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    push_ack_src_bfm<data8St, sc_bv<9>> out8_bfm;
    push_ack_src_bfm<data70St, sc_bv<71>> out70_bfm;

    SC_HAS_PROCESS (bridgeDriver_hdl_sc_wrapper);

    bridgeDriver_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("bridgeDriver_hdl_sc_wrapper", name(), bbMode),
        bridgeDriverBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        out8_bfm("out8_bfm"),
        out70_bfm("out70_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new bridgeDriver_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VbridgeDriver_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->out8_push(out8_hdl_if.push);
        dut_hdl->out8_data(out8_hdl_if.data);
        dut_hdl->out8_ack(out8_hdl_if.ack);
        dut_hdl->out70_push(out70_hdl_if.push);
        dut_hdl->out70_data(out70_hdl_if.data);
        dut_hdl->out70_ack(out70_hdl_if.ack);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        out8_bfm.if_p(out8);
        out8_bfm.hdl_if_p(out8_hdl_if);
        out8_bfm.clk(clk);
        out8_bfm.rst_n(rst_n);

        out70_bfm.if_p(out70);
        out70_bfm.hdl_if_p(out70_hdl_if);
        out70_bfm.clk(clk);
        out70_bfm.rst_n(rst_n);

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

    push_ack_hdl_if<sc_bv<9>> out8_hdl_if;
    push_ack_hdl_if<sc_bv<71>> out70_hdl_if;

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

#endif // BRIDGEDRIVER_HDL_SC_WRAPPER_H_
